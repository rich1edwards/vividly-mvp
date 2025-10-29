#!/usr/bin/env python3
"""
OER Content Ingestion Pipeline Orchestrator

Runs the complete 5-stage pipeline:
1. Download OpenStax textbooks
2. Process CNXML to JSON
3. Chunk content (500 words with overlap)
4. Generate embeddings (Vertex AI)
5. Create vector index (Vertex AI Vector Search)
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse


class PipelineRunner:
    """Orchestrates the OER content ingestion pipeline."""

    def __init__(self, script_dir: Path):
        """
        Initialize pipeline runner.

        Args:
            script_dir: Directory containing pipeline scripts
        """
        self.script_dir = script_dir
        self.stages = [
            {
                'name': 'Download',
                'script': '01_download_openstax.sh',
                'description': 'Download OpenStax textbooks in CNXML format'
            },
            {
                'name': 'Process',
                'script': '02_process_content.py',
                'description': 'Parse CNXML and extract structured content'
            },
            {
                'name': 'Chunk',
                'script': '03_chunk_content.py',
                'description': 'Split content into 500-word chunks'
            },
            {
                'name': 'Embed',
                'script': '04_generate_embeddings.py',
                'description': 'Generate 768-dim embeddings using Vertex AI'
            },
            {
                'name': 'Index',
                'script': '05_create_vector_index.py',
                'description': 'Create and deploy vector search index'
            }
        ]

    def run_stage(self, stage: dict) -> bool:
        """
        Run a single pipeline stage.

        Args:
            stage: Stage configuration dict

        Returns:
            True if successful, False otherwise
        """
        script_path = self.script_dir / stage['script']

        print("")
        print("=" * 70)
        print(f"Stage: {stage['name']}")
        print(f"Description: {stage['description']}")
        print("=" * 70)
        print("")

        # Determine how to run script
        if script_path.suffix == '.sh':
            # Bash script
            cmd = ['bash', str(script_path)]
        else:
            # Python script
            cmd = [sys.executable, str(script_path)]

        # Run script
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.script_dir),
                check=True,
                text=True
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"\n✗ Stage '{stage['name']}' failed with exit code {e.returncode}")
            return False

        except Exception as e:
            print(f"\n✗ Stage '{stage['name']}' failed: {e}")
            return False

    def run_full_pipeline(self, start_stage: int = 1, end_stage: int = 5) -> bool:
        """
        Run the complete pipeline or a subset of stages.

        Args:
            start_stage: Starting stage number (1-5)
            end_stage: Ending stage number (1-5)

        Returns:
            True if all stages successful, False otherwise
        """
        print("")
        print("=" * 70)
        print("OER Content Ingestion Pipeline")
        print("=" * 70)
        print("")
        print(f"Running stages {start_stage}-{end_stage}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

        start_time = datetime.now()

        # Run selected stages
        for i, stage in enumerate(self.stages[start_stage - 1:end_stage], start=start_stage):
            success = self.run_stage(stage)

            if not success:
                print("")
                print("=" * 70)
                print("✗ Pipeline Failed")
                print("=" * 70)
                print(f"Failed at stage {i}: {stage['name']}")
                print("")
                return False

        # Success
        duration = datetime.now() - start_time
        minutes = duration.total_seconds() / 60

        print("")
        print("=" * 70)
        print("✓ Pipeline Complete")
        print("=" * 70)
        print(f"Duration: {minutes:.1f} minutes")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

        return True

    def print_pipeline_info(self):
        """Print pipeline stages and descriptions."""
        print("")
        print("=" * 70)
        print("OER Content Ingestion Pipeline")
        print("=" * 70)
        print("")
        print("Stages:")
        for i, stage in enumerate(self.stages, start=1):
            print(f"{i}. {stage['name']}: {stage['description']}")
            print(f"   Script: {stage['script']}")
            print("")


def check_prerequisites():
    """Check if prerequisites are met."""
    errors = []

    # Check Google Cloud project
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        errors.append("GOOGLE_CLOUD_PROJECT environment variable not set")

    # Check credentials
    creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds:
        errors.append("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    elif not Path(creds).exists():
        errors.append(f"Credentials file not found: {creds}")

    if errors:
        print("✗ Prerequisites not met:")
        for error in errors:
            print(f"  - {error}")
        print("")
        print("Setup instructions:")
        print("  export GOOGLE_CLOUD_PROJECT=vividly-dev-rich")
        print("  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
        print("")
        return False

    print("✓ Prerequisites check passed")
    print(f"  Project: {project_id}")
    print(f"  Credentials: {creds}")
    print("")
    return True


def main():
    """Main pipeline orchestration."""
    parser = argparse.ArgumentParser(
        description='Run OER content ingestion pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python run_pipeline.py

  # Run stages 1-3 only
  python run_pipeline.py --start 1 --end 3

  # Resume from stage 4
  python run_pipeline.py --start 4

  # Show pipeline info
  python run_pipeline.py --info

  # Skip prerequisites check (not recommended)
  python run_pipeline.py --skip-prereqs
        """
    )

    parser.add_argument(
        '--start',
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help='Starting stage (1-5)'
    )

    parser.add_argument(
        '--end',
        type=int,
        default=5,
        choices=[1, 2, 3, 4, 5],
        help='Ending stage (1-5)'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Print pipeline information and exit'
    )

    parser.add_argument(
        '--skip-prereqs',
        action='store_true',
        help='Skip prerequisites check (not recommended)'
    )

    args = parser.parse_args()

    # Get script directory
    script_dir = Path(__file__).parent

    # Initialize runner
    runner = PipelineRunner(script_dir)

    # Show info if requested
    if args.info:
        runner.print_pipeline_info()
        sys.exit(0)

    # Check prerequisites
    if not args.skip_prereqs:
        if not check_prerequisites():
            sys.exit(1)

    # Validate stage range
    if args.start > args.end:
        print("✗ Error: Start stage must be <= end stage")
        sys.exit(1)

    # Run pipeline
    success = runner.run_full_pipeline(args.start, args.end)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
