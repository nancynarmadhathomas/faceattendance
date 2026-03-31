use tract_onnx::prelude::*;
use serde::{Serialize, Deserialize};
use clap::{Parser, Subcommand};
use image::{imageops::FilterType, GenericImageView};
use std::sync::OnceLock;

type RunnableModel = tract_onnx::prelude::SimplePlan<
    tract_onnx::prelude::TypedFact,
    Box<dyn tract_onnx::prelude::TypedOp>,
    tract_onnx::prelude::Graph<tract_onnx::prelude::TypedFact, Box<dyn tract_onnx::prelude::TypedOp>>
>;

static EMBED_MODEL: OnceLock<RunnableModel> = OnceLock::new();
static DETECT_MODEL: OnceLock<RunnableModel> = OnceLock::new();

fn init_embed_model() -> std::result::Result<(), String> {
    if EMBED_MODEL.get().is_some() { return Ok(()); }
    let potential_paths = ["models/mobilefacenet.onnx", "rust-face-engine/models/mobilefacenet.onnx", "../models/mobilefacenet.onnx"];
    for path in potential_paths {
        if let Ok(m) = tract_onnx::onnx().model_for_path(path) {
            if let Ok(runnable) = m.into_optimized().and_then(|m| m.into_runnable()) {
                let _ = EMBED_MODEL.set(runnable);
                return Ok(());
            }
        }
    }
    Err("Embed model not loaded".to_string())
}

fn init_detect_model() -> std::result::Result<(), String> {
    if DETECT_MODEL.get().is_some() { return Ok(()); }
    let potential_paths = ["models/blazeface.onnx", "rust-face-engine/models/blazeface.onnx", "../models/blazeface.onnx"];
    for path in potential_paths {
        if let Ok(m) = tract_onnx::onnx().model_for_path(path) {
            if let Ok(runnable) = m.into_optimized().and_then(|m| m.into_runnable()) {
                let _ = DETECT_MODEL.set(runnable);
                return Ok(());
            }
        }
    }
    Err("Detect model not loaded".to_string())
}

#[derive(Parser)]
#[command(name = "rust-face-engine")]
#[command(about = "Face recognition engine", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate embedding for an image
    Embed {
        #[arg(short, long)]
        image: String,
    },
    /// Detect and crop face
    Detect {
        #[arg(short, long)]
        image: String,
        #[arg(short, long)]
        output: String, // Output path for cropped image
    },
    /// Compare two embeddings
    Compare {
        #[arg(short, long)]
        emb1: String,
        #[arg(short, long)]
        emb2: String,
    },
}

#[derive(Serialize, Deserialize)]
pub struct Result {
    success: bool,
    embedding: Option<Vec<f32>>,
    distance: Option<f32>,
    message: String,
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Embed { image } => {
            let _ = init_embed_model();
            let res = generate_embedding(image);
            println!("{}", serde_json::to_string(&res)?);
        }
        Commands::Detect { image, output } => {
            let _ = init_detect_model();
            let res = detect_and_crop(image, output);
            println!("{}", serde_json::to_string(&res)?);
        }
        Commands::Compare { emb1, emb2 } => {
            let e1: Vec<f32> = serde_json::from_str(emb1).unwrap_or_default();
            let e2: Vec<f32> = serde_json::from_str(emb2).unwrap_or_default();
            let dist = cosine_similarity(&e1, &e2);
            println!("{}", serde_json::to_string(&Result { success: true, embedding: None, distance: Some(dist), message: "OK".to_string() })?);
        }
    }

    Ok(())
}

fn detect_and_crop(image_path: &str, output_path: &str) -> Result {
    let model = match DETECT_MODEL.get() {
        Some(m) => m,
        None => return Result { success: false, embedding: None, distance: None, message: "Detect model not loaded".to_string() },
    };

    let img = match image::open(image_path) {
        Ok(i) => i,
        Err(e) => return Result { success: false, embedding: None, distance: None, message: format!("IO Error: {}", e) },
    };

    let (w, h) = img.dimensions();
    let resized = img.resize_exact(128, 128, FilterType::Triangle).to_rgb8();
    let tensor: Tensor = tract_ndarray::Array4::from_shape_fn((1, 3, 128, 128), |(_, c, y, x)| {
        let pixel = resized.get_pixel(x as u32, y as u32);
        (pixel[c] as f32 / 127.5) - 1.0
    }).into();

    let outputs = model.run(tvec!(tensor.into())).unwrap();
    // BlazeFace outputs: [1, 896, 1] (scores), [1, 896, 16] (boxes/landmarks)
    let scores = outputs[0].to_array_view::<f32>().unwrap();
    let boxes = outputs[1].to_array_view::<f32>().unwrap();

    let mut best_score = 0.0;
    let mut best_idx = 0;

    for i in 0..896 {
        let score = 1.0 / (1.0 + (-(scores[[0, i, 0]])).exp()); // sigmoid
        if score > best_score {
            best_score = score;
            best_idx = i;
        }
    }

    if best_score < 0.5 {
        return Result { success: false, embedding: None, distance: None, message: "No face detected".to_string() };
    }

    // Extract bounding box from [1, 896, 16]
    // Normalized coordinates [ymin, xmin, ymax, xmax] are usually at indices 0,1,2,3 for this model
    let y1 = (boxes[[0, best_idx, 0]] * h as f32) as u32;
    let x1 = (boxes[[0, best_idx, 1]] * w as f32) as u32;
    let y2 = (boxes[[0, best_idx, 2]] * h as f32) as u32;
    let x2 = (boxes[[0, best_idx, 3]] * w as f32) as u32;

    // Add padding (20%)
    let pad_h = (y2.saturating_sub(y1) as f32 * 0.2) as u32;
    let pad_w = (x2.saturating_sub(x1) as f32 * 0.2) as u32;

    let y1 = y1.saturating_sub(pad_h);
    let x1 = x1.saturating_sub(pad_w);
    let y2 = (y2 + pad_h).min(h);
    let x2 = (x2 + pad_w).min(w);

    if x2 <= x1 || y2 <= y1 {
        return Result { success: false, embedding: None, distance: None, message: "Invalid crop".to_string() };
    }

    let crop = img.view(x1, y1, x2 - x1, y2 - y1).to_image();
    if let Err(e) = crop.save(output_path) {
        return Result { success: false, embedding: None, distance: None, message: format!("Save error: {}", e) };
    }

    Result { success: true, embedding: None, distance: None, message: "Face detected and cropped".to_string() }
}

fn generate_embedding(image_path: &str) -> Result {
     let model = match EMBED_MODEL.get() {
        Some(m) => m,
        None => return Result { success: false, embedding: None, distance: None, message: "Embed model not loaded".to_string() },
    };
    let img = match image::open(image_path) {
        Ok(i) => i.resize_exact(112, 112, FilterType::Triangle).to_rgb8(),
        Err(e) => return Result { success: false, embedding: None, distance: None, message: e.to_string() },
    };
    let tensor: Tensor = tract_ndarray::Array4::from_shape_fn((1, 3, 112, 112), |(_, c, y, x)| {
        let pixel = img.get_pixel(x as u32, y as u32);
        (pixel[c] as f32 - 127.5) / 128.0
    }).into();
    let result = model.run(tvec!(tensor.into())).unwrap();
    let embedding: Vec<f32> = result[0].to_array_view::<f32>().unwrap().iter().cloned().collect();
    Result { success: true, embedding: Some(embedding), distance: None, message: "OK".to_string() }
}

fn cosine_similarity(e1: &[f32], e2: &[f32]) -> f32 {
    let dot: f32 = e1.iter().zip(e2.iter()).map(|(a, b)| a * b).sum();
    let norm1: f32 = e1.iter().map(|a| a * a).sum::<f32>().sqrt();
    let norm2: f32 = e2.iter().map(|a| a * a).sum::<f32>().sqrt();
    dot / (norm1 * norm2)
}
