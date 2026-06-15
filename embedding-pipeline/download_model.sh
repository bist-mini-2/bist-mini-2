#!/bin/bash
MODEL_DIR="models/Qwen3-Embedding-4B"
mkdir -p "$MODEL_DIR/1_Pooling"

BASE_URL="https://huggingface.co/Qwen/Qwen3-Embedding-4B/resolve/main"

files=(
  ".gitattributes"
  "config.json"
  "config_sentence_transformers.json"
  "generation_config.json"
  "merges.txt"
  "model.safetensors.index.json"
  "modules.json"
  "tokenizer.json"
  "tokenizer_config.json"
  "vocab.json"
  "model-00001-of-00002.safetensors"
  "model-00002-of-00002.safetensors"
)

echo "🚀 curl을 이용해 Qwen3-Embedding-4B 원본 가중치 다운로드를 개시합니다..."

for file in "${files[@]}"; do
  echo "📥 다운로드 중: $file"
  curl -L -C - "$BASE_URL/$file" -o "$MODEL_DIR/$file"
done

echo "📥 다운로드 중: 1_Pooling/config.json"
curl -L -C - "$BASE_URL/1_Pooling/config.json" -o "$MODEL_DIR/1_Pooling/config.json"

echo "✅ 모든 모델 가중치 및 설정 파일 다운로드 완료!"
