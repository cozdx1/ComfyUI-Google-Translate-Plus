"""Run explicitly to install the original OPUS-MT model as CTranslate2 INT8."""
import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

SOURCE_URL = "https://object.pouta.csc.fi/Tatoeba-MT-models/kor-eng/opusTCv20210807-sepvoc_transformer-big_2022-07-28.zip"
SOURCE_SHA256 = "9132ed606b6964656520931d96a4a6afc7ddc7d55ca5438e1d403db0c05492ef"
MODEL_NAME = "opus-mt-tc-big-ko-en-int8"
WEIGHTS = "opusTCv20210807-sepvoc.spm32k-spm32k.transformer-big.model1.npz.best-perplexity.npz"
VOCABS = ["opusTCv20210807-sepvoc.spm32k-spm32k.src.vocab", "opusTCv20210807-sepvoc.spm32k-spm32k.trg.vocab"]
REQUIRED = ["model.bin", "config.json", "source.spm", "target.spm", "source_vocabulary.json", "target_vocabulary.json"]


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def install(models_dir, archive_path=None):
    destination = Path(models_dir).resolve() / "translation" / MODEL_NAME
    if destination.exists():
        if all((destination / name).is_file() for name in REQUIRED):
            print(f"Already installed: {destination}")
            return destination
        raise ValueError(f"Incomplete model folder: {destination}. Move it aside before reinstalling.")
    try:
        import ctranslate2
    except (ImportError, OSError):
        raise ValueError("Install ctranslate2 and sentencepiece with ComfyUI's Python first. See README.") from None
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="opus-install-", dir=destination.parent) as temporary:
        work = Path(temporary)
        if archive_path is None:
            archive = work / "source.zip"
            print("Downloading original OPUS-MT model (approximately 777 MB)...", flush=True)
            with urllib.request.urlopen(SOURCE_URL, timeout=60) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output, length=8 * 1024 * 1024)
        else:
            archive = Path(archive_path).resolve()
        if digest(archive) != SOURCE_SHA256:
            raise ValueError("Source archive checksum mismatch. The download was not used.")
        # Extract only named files to known paths; archive paths are never used.
        with zipfile.ZipFile(archive) as source:
            for name in [WEIGHTS, *VOCABS, "source.spm", "target.spm", "LICENSE", "README.md"]:
                with source.open(name) as input_file, (work / name).open("wb") as output:
                    shutil.copyfileobj(input_file, output)
        paths = []
        for name in VOCABS:
            path = work / (name + ".yaml")
            tokens = (work / name).read_text(encoding="utf-8").splitlines()
            path.write_text("\n".join("'" + token.replace("'", "''") + "': " + str(index)
                                      for index, token in enumerate(tokens)), encoding="utf-8")
            paths.append(str(path))
        output = work / "converted"
        print("Converting original Marian weights to CPU INT8...", flush=True)
        ctranslate2.converters.MarianConverter(str(work / WEIGHTS), paths).convert(str(output), quantization="int8")
        for name in ["source.spm", "target.spm", "LICENSE", "README.md"]:
            shutil.copy2(work / name, output / name)
        metadata = {"source_url": SOURCE_URL, "source_sha256": SOURCE_SHA256,
                    "ctranslate2_version": ctranslate2.__version__, "quantization": "int8", "license": "CC-BY-4.0"}
        (output / "installation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        output.rename(destination)
    print(f"Installed: {destination}")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-dir", required=True, type=Path, help="ComfyUI models directory")
    parser.add_argument("--archive", type=Path, help="Use an already downloaded original archive")
    args = parser.parse_args()
    try:
        install(args.models_dir, args.archive)
    except (ValueError, OSError, zipfile.BadZipFile, KeyError) as error:
        parser.exit(1, f"Installation failed: {error}\n")


if __name__ == "__main__":
    main()
