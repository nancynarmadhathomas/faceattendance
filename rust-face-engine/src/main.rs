use std::path::Path;
use tract_onnx::prelude::*;
use serde::{Serialize, Deserialize};
use clap::{Parser, Subcommand};
use nalgebra::{DMatrix, DVector};
use image::{imageops::FilterType, GenericImageView};
use std::fs::File;
use std::io::Read;
use std::sync::OnceLock;

type RunnableModel = tract_onnx::prelude::SimplePlan<
    tract_onnx::prelude::TypedFact,
    Box<dyn tract_onnx::prelude::TypedOp>,
    tract_onnx::prelude::Graph<tract_onnx::prelude::TypedFact, Box<dyn tract_onnx::prelude::TypedOp>>
>;

static MODEL: OnceLock<RunnableModel> = OnceLock::new();

fn init_model() -> std::result::Result<(), String> {
    if MODEL.get().is_some() {
        return Ok(());
    }
    match tract_onnx::onnx().model_for_path("models/mobilefacenet.onnx") {
        Ok(m) => {
            match m.into_optimized().and_then(|m| m.into_runnable()) {
                Ok(runnable) => {
                    let _ = MODEL.set(runnable);
                    Ok(())
                },
                Err(_) => Err("Face model not loaded".to_string()),
            }
        },
        Err(_) => Err("Face model not loaded".to_string()),
    }
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
    /// Compare two embeddings
    Compare {
        #[arg(short, long)]
        emb1: String, // JSON array string
        #[arg(short, long)]
        emb2: String, // JSON array string
    },
}

#[derive(Serialize, Deserialize)]
struct Result {
    success: bool,
    embedding: Option<Vec<f32>>,
    distance: Option<f32>,
    message: String,
}

fn main() -> anyhow::Result<()> {
    // Initialize model once on startup and store in global state
    let model_status = init_model();

    let cli = Cli::parse();

    match &cli.command {
        Commands::Embed { image } => {
            if let Err(_) = model_status {
                let res = Result {
                    success: false,
                    embedding: None,
                    distance: None,
                    message: "Face model not loaded".to_string(),
                };
                println!("{}", serde_json::to_string(&res)?);
                return Ok(());
            }
            let res = generate_embedding(image);
            println!("{}", serde_json::to_string(&res)?);
        }
        Commands::Compare { emb1, emb2 } => {
            let e1: Vec<f32> = serde_json::from_str(emb1)?;
            let e2: Vec<f32> = serde_json::from_str(emb2)?;
            let dist = cosine_similarity(&e1, &e2);
            let res = Result {
                success: true,
                embedding: None,
                distance: Some(dist),
                message: "Comparison successful".to_string(),
            };
            println!("{}", serde_json::to_string(&res)?);
        }
    }

    Ok(())
}

fn generate_embedding(image_path: &str) -> Result {
    let model = match MODEL.get() {
        Some(m) => m,
        None => return Result {
            success: false,
            embedding: None,
            distance: None,
            message: "Face model not loaded".to_string(),
        },
    };

    let img = match image::open(image_path) {
        Ok(i) => i.resize_exact(112, 112, FilterType::Triangle).to_rgb8(),
        Err(e) => return Result {
            success: false,
            embedding: None,
            distance: None,
            message: format!("Failed to open image: {}", e),
        },
    };

    let tensor: Tensor = tract_ndarray::Array4::from_shape_fn((1, 3, 112, 112), |(_, c, y, x)| {
        let pixel = img.get_pixel(x as u32, y as u32);
        (pixel[c] as f32 - 127.5) / 128.0
    }).into();

    let result = model.run(tvec!(tensor)).unwrap();
    let embedding: Vec<f32> = result[0]
        .to_array_view::<f32>().unwrap()
        .iter()
        .cloned()
        .collect();

    Result {
        success: true,
        embedding: Some(embedding),
        distance: None,
        message: "Embedding generated".to_string(),
    }
}

fn cosine_similarity(e1: &[f32], e2: &[f32]) -> f32 {
    let dot: f32 = e1.iter().zip(e2.iter()).map(|(a, b)| a * b).sum();
    let norm1: f32 = e1.iter().map(|a| a * a).sum::<f32>().sqrt();
    let norm2: f32 = e2.iter().map(|a| a * a).sum::<f32>().sqrt();
    dot / (norm1 * norm2)
}
