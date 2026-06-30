import argparse
import sys
import os
import json
from src.utils.loader import load_config
from src.pipeline import CandidateTransformationPipeline
from src.utils.logger import get_logger
from src.utils.exceptions import CandidateTransformerError

logger = get_logger("CLI")

def main():
    parser = argparse.ArgumentParser(
        description="Candidate Transformation Engine CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python -m src.cli.main \\
    --csv recruiter.csv \\
    --ats ats.json \\
    --resume resume.pdf \\
    --notes recruiter_notes.txt \\
    --github https://github.com/username \\
    --config config/default.json
        """
    )
    
    # Input Sources
    parser.add_argument("--csv", help="Path to structured Recruiter CSV export file.")
    parser.add_argument("--ats", help="Path to ATS JSON blob export file.")
    parser.add_argument("--resume", help="Path to unstructured candidate Resume PDF.")
    parser.add_argument("--notes", help="Path to unstructured Recruiter Notes text file.")
    parser.add_argument("--github", help="URL to candidate verified GitHub profile.")
    
    # Configuration & Output
    parser.add_argument("--config", required=True, help="Path to custom output projection config JSON.")
    parser.add_argument("--output", help="Optional path to write the transformed candidate JSON profile. Prints to stdout by default.")

    args = parser.parse_args()

    # 1. Validation: Ensure at least one input source is provided
    sources = [args.csv, args.ats, args.resume, args.notes, args.github]
    if not any(sources):
        logger.error("Error: At least one input source (--csv, --ats, --resume, --notes, or --github) must be provided.")
        sys.exit(1)

    # 2. Validation: Ensure all local source files exist
    local_sources = [
        ("--csv", args.csv),
        ("--ats", args.ats),
        ("--resume", args.resume),
        ("--notes", args.notes),
        ("--config", args.config)
    ]
    for arg_name, path in local_sources:
        if path and not os.path.exists(path):
            logger.error(f"Error: Specified file for {arg_name} does not exist: {path}")
            sys.exit(1)

    try:
        # Load configuration
        config = load_config(args.config)
        
        # Instantiate pipeline and run transformation
        pipeline = CandidateTransformationPipeline()
        output_data = pipeline.run(
            config=config,
            csv_path=args.csv,
            ats_path=args.ats,
            resume_path=args.resume,
            notes_path=args.notes,
            github_url=args.github
        )
        
        formatted_json = json.dumps(output_data, indent=2)

        if args.output:
            # Check if output directory exists
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_json)
            logger.info(f"Successfully wrote candidate profile to {args.output}")
        else:
            print(formatted_json)

    except CandidateTransformerError as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
