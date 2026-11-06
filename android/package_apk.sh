#!/usr/bin/env bash
set -e

BUILD_TOOLS="/home/zoth/Android/Sdk/build-tools/35.0.0"
PLATFORM="/home/zoth/Android/Sdk/platforms/android-34/android.jar"
KEYSTORE="$HOME/.android/debug.keystore"
SRC_ROOT="/home/zoth/NullAITech/zoth-cursorz/android"
APP_ROOT="$SRC_ROOT/app/src/main"

echo "==> 1. Preparing clean build directory..."
rm -rf "$SRC_ROOT/build"
mkdir -p "$SRC_ROOT/build/compiled_res" "$SRC_ROOT/build/gen" "$SRC_ROOT/build/classes" "$SRC_ROOT/build/apk_unaligned" "$SRC_ROOT/dist"

echo "==> 2. Compiling Android resources with AAPT2..."
"$BUILD_TOOLS/aapt2" compile --dir "$APP_ROOT/res" -o "$SRC_ROOT/build/compiled_res/resources.zip"

echo "==> 3. Linking APK and generating R.java..."
"$BUILD_TOOLS/aapt2" link "$SRC_ROOT/build/compiled_res/resources.zip" \
  -I "$PLATFORM" \
  --manifest "$APP_ROOT/AndroidManifest.xml" \
  --java "$SRC_ROOT/build/gen" \
  --min-sdk-version 26 \
  --target-sdk-version 34 \
  -o "$SRC_ROOT/build/apk_unaligned/res.apk" \
  --auto-add-overlay

echo "==> 4. Compiling Java sources with javac (JDK 21 -source 17)..."
/usr/lib/jvm/java-1.21.0-openjdk-amd64/bin/javac -source 17 -target 17 -d "$SRC_ROOT/build/classes" \
  -cp "$PLATFORM" \
  $(find "$SRC_ROOT/build/gen" "$APP_ROOT/java" -name "*.java")

echo "==> 5. Compiling bytecode to DEX with D8..."
"$BUILD_TOOLS/d8" --release --min-api 26 \
  --output "$SRC_ROOT/build/classes" \
  --lib "$PLATFORM" \
  $(find "$SRC_ROOT/build/classes" -name "*.class")

echo "==> 6. Packaging DEX and assets into APK..."
cp "$SRC_ROOT/build/apk_unaligned/res.apk" "$SRC_ROOT/build/unaligned.apk"
cd "$SRC_ROOT/build/classes" && zip -uj "$SRC_ROOT/build/unaligned.apk" classes.dex
cd "$APP_ROOT" && zip -r -u "$SRC_ROOT/build/unaligned.apk" assets/

echo "==> 7. Zipaligning APK (4-byte alignment)..."
"$BUILD_TOOLS/zipalign" -f -v -p 4 "$SRC_ROOT/build/unaligned.apk" "$SRC_ROOT/build/zoth-cursorz-aligned.apk"

echo "==> 8. Signing APK with apksigner (v1 + v2 + v3 schemes)..."
"$BUILD_TOOLS/apksigner" sign --ks "$KEYSTORE" \
  --ks-pass pass:android \
  --key-pass pass:android \
  --v1-signing-enabled true \
  --v2-signing-enabled true \
  --v3-signing-enabled true \
  --out "$SRC_ROOT/dist/zoth-cursorz-arm64.apk" \
  "$SRC_ROOT/build/zoth-cursorz-aligned.apk"

echo "==> 9. Verifying APK signature..."
"$BUILD_TOOLS/apksigner" verify --verbose "$SRC_ROOT/dist/zoth-cursorz-arm64.apk"

echo "==> SUCCESS: Created signed, verified zoth-cursorz-arm64.apk"
ls -lh "$SRC_ROOT/dist/zoth-cursorz-arm64.apk"
