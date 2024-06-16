from serve import CatHeader
from pathlib import Path
from os import PathLike
from loguru import logger
import click


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
def main(input_file: PathLike):
    with open(input_file, "rb") as f:
        data = f.read()
    for i, cat in enumerate(CatHeader.iter_stream(data)):
        logger.info(f"cat {i} len {len(cat)}")


if __name__ == "__main__":
    main() # pylint: disable=no-value-for-parameter
