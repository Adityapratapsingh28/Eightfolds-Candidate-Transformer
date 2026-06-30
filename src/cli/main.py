import argparse
import sys
import json
from src.utils.loader import load_config
from src.pipeline import CandidateTransformationPipeline
from src.utils.logger import get_logger
from src.utils.exceptions import CandidateTransformerError

logger = get_logger("CLI")

def main():
    parser = argparse.ArgumentParser(description="Candidate Transformation Engine CLI")
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Paths to one or more candidate source files (CSV, JSON, PDF, TXT)."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the JSON projection configuration file."
    )
    parser.add_argument(
        "--output",
        help="Optional path to write the transformed candidate JSON profile. Prints to stdout if not specified."
    )

    args = parser.parse_args()

    try:
        # Load custom projection configuration
        config = load_config(args.config)
        
        # Instantiate pipeline and run transformation
        pipeline = CandidateTransformationPipeline()
        output_data = pipeline.run(args.inputs, config)
        
        # Format the output JSON
        formatted_json = json.dumps(output_data, indent=2)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_json)
            logger.info(f"Successfully wrote candidate profile to {args.output}")
        else:
            print(formatted_json)

    except CandidateTransformerError as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

