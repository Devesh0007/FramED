"""FramED CLI — encode any file into a high-density data video or decode it back."""
import click
from framed.pipeline import encode_file, decode_file


@click.group()
@click.version_option("0.1.0", prog_name="FramED")
def cli():
    """
    FramED — Visual Data-Storage Protocol.

    Encode ANY file into a high-density video and decode it back
    byte-for-byte. Uses Zstandard compression, optional AES-256-GCM encryption,
    and XOR parity for robustness.
    """


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False))
@click.argument('output_video')
@click.option(
    '--mode', '-m',
    type=click.Choice(['archive', 'optical', 'youtube']),
    default='archive', show_default=True,
    help='archive=1x1 RGB cells (4K lossless); optical=8x8 RGB cells (1080p); youtube=2x2 RGB 1-bit cells (compression-resilient)',
)
@click.option(
    '--password', '-p',
    default=None,
    help='Encrypt with AES-256-GCM (omit to skip encryption)',
)
def encode(input_file, output_video, mode, password):
    """Encode INPUT_FILE into OUTPUT_VIDEO (.avi, lossless FFV1)."""
    try:
        out = encode_file(input_file, output_video, mode_name=mode, password=password)
        click.secho(f"[OK] Done: {out}", fg='green', bold=True)
    except Exception as e:
        click.secho(f"[ERROR] Encode failed: {e}", fg='red', bold=True)


@cli.command()
@click.argument("input_video", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--mode", help="Force decode mode ('archive', 'optical', or 'youtube'). Usually auto-detected from MANIFEST.")
@click.option("--password", help="Password if the file was encrypted.")
def decode(input_video, output_dir, mode, password):
    """Decode INPUT_VIDEO back into original file inside OUTPUT_DIR."""
    try:
        out = decode_file(input_video, output_dir, mode_name=mode, password=password)
        click.secho(f"\n[OK] Done: {out}", fg='green', bold=True)
    except Exception as e:
        click.secho(f"\n[ERROR] Decode failed: {e}", fg='red', bold=True)


if __name__ == '__main__':
    cli()
