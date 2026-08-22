from pathlib import Path
import json
import traceback
import cv2
import fitz
import numpy as np

from PySide6.QtCore import (
    QThread,
    Signal,
)

from preprocess import (
    deskew_and_warp
)

from recognizer import (
    LocalHandwritingRecognizer
)

from extract import (
    extract_page
)

from excel_export import (
    build_workbook
)


class TranscriptionWorker(
    QThread
):

    # percentage, message
    progress = Signal(
        int,
        str
    )

    # General status
    status = Signal(
        str
    )

    # Preview of first aligned page
    preview_ready = Signal(
        object
    )

    # All aligned pages.
    pages_ready = Signal(
        object
    )

    # results, review items, output path
    completed = Signal(
        object,
        object,
        str
    )

    failed = Signal(
        str
    )


    def __init__(
        self,
        input_path,
        output_path,
        template_path=None
    ):

        super().__init__()

        self.input_path = (
            Path(input_path)
        )

        self.output_path = (
            Path(output_path)
        )

        self.template_path = (
            template_path
        )


    def load_pages(self):

        suffix = (
            self.input_path
            .suffix
            .lower()
        )

        if suffix == ".pdf":

            document = fitz.open(
                self.input_path
            )

            pages = []

            for page in document:

                pixmap = (
                    page.get_pixmap(
                        matrix=fitz.Matrix(
                            2,
                            2
                        ),
                        alpha=False
                    )
                )

                array = np.frombuffer(
                    pixmap.samples,
                    dtype=np.uint8
                )

                rgb = array.reshape(
                    pixmap.height,
                    pixmap.width,
                    3
                )

                bgr = cv2.cvtColor(
                    rgb,
                    cv2.COLOR_RGB2BGR
                )

                pages.append(
                    bgr
                )

            return pages


        image = cv2.imread(
            str(self.input_path)
        )

        if image is None:

            raise ValueError(
                "Could not open input file."
            )

        return [image]


    def run(self):

        try:

            # -----------------
            # LOAD FORM
            # -----------------

            self.progress.emit(
                2,
                "Loading form"
            )

            pages = (
                self.load_pages()
            )


            # -----------------
            # LOAD MODEL
            # -----------------

            self.progress.emit(
                5,
                "Loading local handwriting model"
            )

            self.status.emit(
                "Loading TrOCR locally..."
            )

            recognizer = (
                LocalHandwritingRecognizer()
            )


            # -----------------
            # PROCESS PAGES
            # -----------------

            all_results = []

            all_review_items = []

            aligned_pages = []

            total_pages = len(
                pages
            )


            for (
                page_number,
                page
            ) in enumerate(
                pages,
                start=1
            ):

                self.status.emit(
                    (
                        f"Aligning page "
                        f"{page_number} "
                        f"of "
                        f"{total_pages}"
                    )
                )

                aligned = (
                    deskew_and_warp(
                        page
                    )
                )

                aligned_pages.append(
                    aligned
                )


                # Send first page to preview.
                if page_number == 1:

                    self.preview_ready.emit(
                        aligned
                    )


                def field_progress(
                    completed,
                    total,
                    message
                ):

                    # OCR occupies 5% to 90%.
                    page_size = (
                        85
                        /
                        total_pages
                    )

                    page_base = (
                        5
                        +
                        (
                            page_number - 1
                        )
                        *
                        page_size
                    )

                    percent = (
                        page_base
                        +
                        (
                            completed
                            /
                            total
                        )
                        *
                        page_size
                    )

                    self.progress.emit(
                        int(percent),
                        message
                    )


                results, review_items = (
                    extract_page(
                        aligned,
                        recognizer,
                        page_number=page_number,
                        progress_callback=field_progress
                    )
                )

                all_results.extend(
                    results
                )

                all_review_items.extend(
                    review_items
                )


            # -----------------
            # EXPORT
            # -----------------

            self.progress.emit(
                92,
                "Creating Excel workbook"
            )

            build_workbook(
                all_results,
                self.output_path,
                template_path=self.template_path
            )


            # -----------------
            # SAVE DEBUG DATA
            # -----------------

            self.progress.emit(
                96,
                "Saving transcription data"
            )

            json_path = (
                self.output_path
                .with_suffix(
                    ".json"
                )
            )

            json_path.write_text(
                json.dumps(
                    {
                        "results":
                            all_results,

                        "manual_review":
                            all_review_items,
                    },
                    indent=2
                ),
                encoding="utf-8"
            )


            # -----------------
            # COMPLETE
            # -----------------

            self.progress.emit(
                100,
                "Complete"
            )

            self.status.emit(
                "Transcription complete"
            )

            self.pages_ready.emit(
                aligned_pages
            )

            self.completed.emit(
                all_results,
                all_review_items,
                str(
                    self.output_path
                )
            )


        except Exception as error:

            full_error = traceback.format_exc()

            print("\n" + "=" * 70)
            print("TRANSCRIPTION ERROR")
            print("=" * 70)
            print(full_error)
            print("=" * 70 + "\n")

            # Some Python exceptions have an empty str(error).
            # The traceback always contains the actual exception type.
            if not str(error).strip():
                error_message = (
                    f"{type(error).__name__}: {repr(error)}"
                )
            else:
                error_message = str(error)

            self.failed.emit(
                f"{error_message}\n\n"
                f"Full traceback:\n{full_error}"
            )