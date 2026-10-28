"""Start Relayloom. Rehearsal is the default; Meta requires explicit opt-in."""
import argparse
from pathlib import Path

from .controller import Controller
from .server import LocalServer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8800)
    parser.add_argument("--database", type=Path, default=Path("data/relayloom.sqlite3"))
    parser.add_argument("--enable-meta-synthetic", action="store_true", help="Allow billable Meta calls only after explicit environment configuration; synthetic fixture only")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if args.enable_meta_synthetic:
        from .meta import MetaWorker
        try:
            worker = MetaWorker.from_environment()
        except (ValueError, OSError) as error:
            parser.error(str(error))
        controller = Controller(args.database, worker=worker)
    else:
        controller = Controller(args.database)
    server = LocalServer(("127.0.0.1", args.port), controller)
    print(f"Relayloom {controller.mode} mode: http://127.0.0.1:{args.port}")
    print("Synthetic specialist outputs. No live inference or external actions." if controller.mode == "rehearsal" else "Meta enabled for the bundled fictional fixture. Run specialists may consume credits. No external actions.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        controller.close()


if __name__ == "__main__":
    main()
