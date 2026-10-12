import argparse
from pathlib import Path
from .common import ROOT, output_dirs, write_json

def main():
    parser = argparse.ArgumentParser(description="NextBrain reproduction and explicitly synthetic demonstrations")
    parser.add_argument("action", choices=["download", "atlas", "probability", "normative", "all", "preflight", "official", "source-probability", "report"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--reference", action="store_true", help="Download optional official FSL MNI152 T1 reference")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--source-directory", type=Path)
    parser.add_argument("--source-file")
    args = parser.parse_args()
    output_dirs(args.root)
    if args.action in ["download", "all"]:
        from .download import download
        download(args.root, reference=args.reference)
    if args.action in ["atlas", "all"]:
        from .atlas import analyze
        from .visualization import visualize
        image, data, lut, regions, metadata = analyze(args.root)
        visualize(args.root, image, lut, regions)
        print(f"Atlas labels: {metadata['nonbackground_regions']}; bilateral pairs: {metadata['matched_bilateral_pairs']}", flush=True)
    if args.action in ["probability", "all"]:
        from .probability import run_synthetic
        print(run_synthetic(args.root), flush=True)
    if args.action in ["normative", "all"]:
        from .normative import run_normative
        result = run_normative(args.root)
        print("SYNTHETIC normative held-out metrics:", result["test_metrics"], flush=True)
    if args.action in ["preflight", "all"]:
        from .official import preflight
        state = preflight()
        write_json(args.root / "results/official_preflight.json", state)
        print("Official CPU preflight:", state, flush=True)
    if args.action == "official":
        if args.input is None or args.output is None or args.threads < 1:
            parser.error("official requires --input, --output and positive --threads")
        from .official import run_official
        run_official(args.input, args.output, args.threads)
    if args.action == "source-probability":
        if args.source_directory is None or args.source_file is None or args.output is None:
            parser.error("source-probability requires --source-directory, --source-file, --output")
        from .probability import inspect_source_probability
        inspect_source_probability(args.source_directory, args.source_file, args.output)
    if args.action == "report":
        from .report import generate_report
        generate_report(args.root)

if __name__ == "__main__":
    main()
