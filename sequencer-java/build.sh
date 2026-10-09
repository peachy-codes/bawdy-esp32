#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 Compiling WLED Universe Manager [Java 17]..."
mvn compile -o

echo "📦 Packaging standalone wled-sequencer.jar..."
mkdir -p target/staging
cp -r target/classes/* target/staging/

(
  cd target/staging
  jar xf ~/.m2/repository/com/fasterxml/jackson/core/jackson-databind/2.15.2/jackson-databind-2.15.2.jar
  jar xf ~/.m2/repository/com/fasterxml/jackson/core/jackson-core/2.15.2/jackson-core-2.15.2.jar
  jar xf ~/.m2/repository/com/fasterxml/jackson/core/jackson-annotations/2.15.2/jackson-annotations-2.15.2.jar
  jar cfe ../wled-sequencer.jar com.wled.sequencer.Main .
)

echo "✅ Build complete: target/wled-sequencer.jar"
