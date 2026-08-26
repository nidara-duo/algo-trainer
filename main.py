"""
Main entry point - launches pywebview window with the Algo Trainer application.
"""

import os
import webview

from api import Api


def main():
    """Launch the Algo Trainer application."""

    base_dir = os.path.dirname(os.path.abspath(__file__))

    api = Api(base_dir)

    index_path = os.path.join(base_dir, "index.html")

    def on_loaded():
        if webview.windows:
            webview.windows[0].evaluate_js("onPywebviewReady()")

    window = webview.create_window(
        title="Algo Trainer",
        url=index_path,
        js_api=api,
        width=1400,
        height=700,
        resizable=True,
        min_size=(800, 600),
        text_select=True
    )

    if window is None:
        raise RuntimeError("Failed to create pywebview window")

    window.events.loaded += on_loaded

    webview.start()


if __name__ == '__main__':
    main()