"""Finestra principale dell'applicazione di conversione file."""

import sys
from pathlib import Path
from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFileDialog, QProgressBar, QGroupBox, QFormLayout,
    QComboBox, QSpinBox, QCheckBox, QTextEdit, QTabWidget,
    QMessageBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QFont, QColor, QIcon

# Aggiungi il percorso del progetto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.worker import ConversionWorker


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione File Converter."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Converter Pro")
        self.setMinimumSize(900, 700)
        
        # Stato dell'applicazione
        self.selected_files: List[str] = []
        self.output_directory: str = ""
        self.worker: ConversionWorker = None
        self.conversion_results: List[Dict[str, Any]] = []
        
        # Setup UI
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Configura l'interfaccia utente."""
        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Splitter per dividere la UI
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # Parte superiore: selezione file e opzioni
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(top_widget)

        # Sezione selezione file
        file_group = QGroupBox("File da convertire")
        file_layout = QHBoxLayout(file_group)
        
        # Lista file
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(150)
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        file_layout.addWidget(self.file_list, stretch=1)

        # Bottoni gestione file
        file_buttons = QVBoxLayout()
        self.add_file_btn = QPushButton("Aggiungi File")
        self.add_folder_btn = QPushButton("Aggiungi Cartella")
        self.remove_file_btn = QPushButton("Rimuovi Selezionati")
        self.clear_all_btn = QPushButton("Pulisci Tutto")
        
        file_buttons.addWidget(self.add_file_btn)
        file_buttons.addWidget(self.add_folder_btn)
        file_buttons.addWidget(self.remove_file_btn)
        file_buttons.addWidget(self.clear_all_btn)
        file_buttons.addStretch()
        file_layout.addLayout(file_buttons)

        top_layout.addWidget(file_group)

        # Sezione opzioni di conversione (tab)
        options_group = QGroupBox("Opzioni di Conversione")
        options_layout = QVBoxLayout(options_group)
        
        self.options_tabs = QTabWidget()
        
        # Tab Immagini
        image_tab = self._create_image_options_tab()
        self.options_tabs.addTab(image_tab, "Immagini")
        
        # Tab Video/Audio
        video_tab = self._create_video_options_tab()
        self.options_tabs.addTab(video_tab, "Video/Audio")
        
        # Tab PDF
        pdf_tab = self._create_pdf_options_tab()
        self.options_tabs.addTab(pdf_tab, "PDF")
        
        options_layout.addWidget(self.options_tabs)
        top_layout.addWidget(options_group)

        # Parte inferiore: output e log
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(bottom_widget)

        # Sezione directory output
        output_group = QGroupBox("Directory di Output")
        output_layout = QHBoxLayout(output_group)
        
        self.output_path_label = QLabel("Nessuna directory selezionata")
        self.output_path_label.setStyleSheet("color: gray;")
        output_layout.addWidget(self.output_path_label, stretch=1)
        
        self.select_output_btn = QPushButton("Seleziona Directory")
        output_layout.addWidget(self.select_output_btn)
        
        self.use_default_output_cb = QCheckBox("Usa cartella 'converted'")
        self.use_default_output_cb.setChecked(True)
        output_layout.addWidget(self.use_default_output_cb)

        bottom_layout.addWidget(output_group)

        # Barra di progresso
        progress_group = QGroupBox("Progresso")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Pronto per la conversione")
        progress_layout.addWidget(self.progress_label)

        bottom_layout.addWidget(progress_group)

        # Log delle operazioni
        log_group = QGroupBox("Log Operazioni")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        bottom_layout.addWidget(log_group)

        # Bottone avvia conversione
        self.convert_btn = QPushButton("Avvia Conversione")
        self.convert_btn.setMinimumHeight(50)
        self.convert_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        bottom_layout.addWidget(self.convert_btn)

        # Imposta dimensioni splitter
        splitter.setSizes([400, 300])

    def _create_image_options_tab(self) -> QWidget:
        """Crea il tab per le opzioni immagini."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Qualità
        self.image_quality_combo = QComboBox()
        self.image_quality_combo.addItems(["Bassa", "Media", "Alta"])
        self.image_quality_combo.setCurrentIndex(1)
        layout.addRow("Qualità:", self.image_quality_combo)
        
        # Resize
        self.resize_enabled_cb = QCheckBox("Abilita resize")
        layout.addRow("", self.resize_enabled_cb)
        
        resize_widget = QWidget()
        resize_layout = QHBoxLayout(resize_widget)
        resize_layout.setContentsMargins(0, 0, 0, 0)
        self.resize_width_spin = QSpinBox()
        self.resize_width_spin.setRange(1, 10000)
        self.resize_width_spin.setValue(1920)
        self.resize_height_spin = QSpinBox()
        self.resize_height_spin.setRange(1, 10000)
        self.resize_height_spin.setValue(1080)
        resize_layout.addWidget(QLabel("Larghezza:"))
        resize_layout.addWidget(self.resize_width_spin)
        resize_layout.addWidget(QLabel("Altezza:"))
        resize_layout.addWidget(self.resize_height_spin)
        resize_layout.addStretch()
        layout.addRow("", resize_widget)
        
        # Scala di grigi
        self.grayscale_cb = QCheckBox("Converti in scala di grigi")
        layout.addRow("", self.grayscale_cb)
        
        # Ottimizzazione
        self.optimize_images_cb = QCheckBox("Ottimizza immagine")
        self.optimize_images_cb.setChecked(True)
        layout.addRow("", self.optimize_images_cb)
        
        return widget

    def _create_video_options_tab(self) -> QWidget:
        """Crea il tab per le opzioni video/audio."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Qualità
        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItems(["Bassa", "Media", "Alta", "Ultra"])
        self.video_quality_combo.setCurrentIndex(1)
        layout.addRow("Qualità:", self.video_quality_combo)
        
        # Codec video
        self.video_codec_combo = QComboBox()
        self.video_codec_combo.addItems(["libx264", "libx265", "vp9", "mpeg4"])
        layout.addRow("Codec Video:", self.video_codec_combo)
        
        # Codec audio
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(["aac", "mp3", "opus", "flac"])
        self.audio_codec_combo.setCurrentIndex(0)
        layout.addRow("Codec Audio:", self.audio_codec_combo)
        
        # Bitrate audio
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems(["64k", "128k", "192k", "256k", "320k"])
        self.audio_bitrate_combo.setCurrentIndex(1)
        layout.addRow("Bitrate Audio:", self.audio_bitrate_combo)
        
        # Resize video
        self.resize_video_enabled_cb = QCheckBox("Abilita resize video")
        layout.addRow("", self.resize_video_enabled_cb)
        
        resize_video_widget = QWidget()
        resize_video_layout = QHBoxLayout(resize_video_widget)
        resize_video_layout.setContentsMargins(0, 0, 0, 0)
        self.resize_video_width_spin = QSpinBox()
        self.resize_video_width_spin.setRange(1, 8000)
        self.resize_video_width_spin.setValue(1920)
        self.resize_video_height_spin = QSpinBox()
        self.resize_video_height_spin.setRange(1, 8000)
        self.resize_video_height_spin.setValue(1080)
        resize_video_layout.addWidget(QLabel("Larghezza:"))
        resize_video_layout.addWidget(self.resize_video_width_spin)
        resize_video_layout.addWidget(QLabel("Altezza:"))
        resize_video_layout.addWidget(self.resize_video_height_spin)
        resize_video_layout.addStretch()
        layout.addRow("", resize_video_widget)
        
        # FPS
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        layout.addRow("FPS:", self.fps_spin)
        
        return widget

    def _create_pdf_options_tab(self) -> QWidget:
        """Crea il tab per le opzioni PDF."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Operazione
        self.pdf_operation_combo = QComboBox()
        self.pdf_operation_combo.addItems([
            "Comprimi", 
            "Dividi in pagine", 
            "Converti in immagini",
            "Unisci PDF"
        ])
        layout.addRow("Operazione:", self.pdf_operation_combo)
        
        # Qualità compressione
        self.pdf_quality_combo = QComboBox()
        self.pdf_quality_combo.addItems(["Bassa", "Media", "Alta"])
        self.pdf_quality_combo.setCurrentIndex(1)
        layout.addRow("Qualità:", self.pdf_quality_combo)
        
        # DPI per conversione immagini
        self.pdf_dpi_spin = QSpinBox()
        self.pdf_dpi_spin.setRange(72, 600)
        self.pdf_dpi_spin.setSingleStep(72)
        self.pdf_dpi_spin.setValue(150)
        layout.addRow("DPI:", self.pdf_dpi_spin)
        
        # Formato output immagini
        self.pdf_image_format_combo = QComboBox()
        self.pdf_image_format_combo.addItems(["png", "jpg", "tiff"])
        layout.addRow("Formato immagini:", self.pdf_image_format_combo)
        
        return widget

    def _setup_connections(self):
        """Configura le connessioni dei segnali."""
        self.add_file_btn.clicked.connect(self._add_files)
        self.add_folder_btn.clicked.connect(self._add_folder)
        self.remove_file_btn.clicked.connect(self._remove_selected_files)
        self.clear_all_btn.clicked.connect(self._clear_all_files)
        self.select_output_btn.clicked.connect(self._select_output_directory)
        self.use_default_output_cb.stateChanged.connect(self._toggle_output_directory)
        self.convert_btn.clicked.connect(self._start_conversion)

    def _add_files(self):
        """Aggiunge file alla lista."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleziona file da convertire",
            "",
            "Tutti i file (*);;"
            "Immagini (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp);;"
            "Video (*.mp4 *.avi *.mkv *.mov *.wmv *.flv);;"
            "Audio (*.mp3 *.wav *.aac *.flac *.ogg);;"
            "PDF (*.pdf)"
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                item = QListWidgetItem(Path(file).name)
                item.setData(Qt.UserRole, file)
                self.file_list.addItem(item)
        
        self._log(f"Aggiunti {len(files)} file", "info")

    def _add_folder(self):
        """Aggiunge tutti i file supportati da una cartella."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleziona cartella",
            ""
        )
        
        if folder:
            supported_extensions = {
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
                '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',
                '.mp3', '.wav', '.aac', '.flac', '.ogg',
                '.pdf'
            }
            
            count = 0
            for file_path in Path(folder).iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    if str(file_path) not in self.selected_files:
                        self.selected_files.append(str(file_path))
                        item = QListWidgetItem(file_path.name)
                        item.setData(Qt.UserRole, str(file_path))
                        self.file_list.addItem(item)
                        count += 1
            
            self._log(f"Aggiunti {count} file dalla cartella", "info")

    def _remove_selected_files(self):
        """Rimuove i file selezionati dalla lista."""
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)
            self.file_list.takeItem(self.file_list.row(item))
        
        self._log(f"Rimossi {len(selected_items)} file", "info")

    def _clear_all_files(self):
        """Pulisce tutta la lista file."""
        self.selected_files.clear()
        self.file_list.clear()
        self._log("Lista file pulita", "info")

    def _select_output_directory(self):
        """Seleziona la directory di output."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleziona directory di output",
            ""
        )
        
        if directory:
            self.output_directory = directory
            self.output_path_label.setText(directory)
            self.output_path_label.setStyleSheet("color: green;")
            self.use_default_output_cb.setChecked(False)
            self._log(f"Directory di output: {directory}", "info")

    def _toggle_output_directory(self, state):
        """Abilita/disabilita l'uso della directory default."""
        if state == Qt.Checked:
            self.output_path_label.setText("Cartella 'converted' (default)")
            self.output_path_label.setStyleSheet("color: blue;")
            self.output_directory = ""
        else:
            self.output_path_label.setText("Nessuna directory selezionata")
            self.output_path_label.setStyleSheet("color: gray;")

    def _get_conversion_options(self) -> Dict[str, Any]:
        """Raccoglie tutte le opzioni di conversione dalla UI."""
        options = {}
        
        # Opzioni immagini
        quality_map = {"Bassa": "low", "Media": "medium", "Alta": "high"}
        options['image_quality'] = quality_map.get(
            self.image_quality_combo.currentText(), 
            'medium'
        )
        options['resize_enabled'] = self.resize_enabled_cb.isChecked()
        options['resize_width'] = self.resize_width_spin.value()
        options['resize_height'] = self.resize_height_spin.value()
        options['grayscale'] = self.grayscale_cb.isChecked()
        options['optimize_images'] = self.optimize_images_cb.isChecked()
        
        # Opzioni video
        video_quality_map = {"Bassa": "low", "Media": "medium", "Alta": "high", "Ultra": "ultra"}
        options['video_quality'] = video_quality_map.get(
            self.video_quality_combo.currentText(),
            'medium'
        )
        options['video_codec'] = self.video_codec_combo.currentText()
        options['audio_codec'] = self.audio_codec_combo.currentText()
        bitrate = self.audio_bitrate_combo.currentText()
        options['audio_bitrate'] = bitrate
        options['resize_video_enabled'] = self.resize_video_enabled_cb.isChecked()
        options['resize_video_width'] = self.resize_video_width_spin.value()
        options['resize_video_height'] = self.resize_video_height_spin.value()
        options['fps'] = self.fps_spin.value()
        
        # Opzioni PDF
        pdf_op_map = {
            "Comprimi": "compress",
            "Dividi in pagine": "split",
            "Converti in immagini": "to_images",
            "Unisci PDF": "merge"
        }
        options['pdf_operation'] = pdf_op_map.get(
            self.pdf_operation_combo.currentText(),
            'compress'
        )
        options['pdf_quality'] = quality_map.get(
            self.pdf_quality_combo.currentText(),
            'medium'
        )
        options['pdf_dpi'] = self.pdf_dpi_spin.value()
        options['pdf_image_format'] = self.pdf_image_format_combo.currentText()
        
        return options

    def _start_conversion(self):
        """Avvia la conversione dei file."""
        if not self.selected_files:
            QMessageBox.warning(self, "Nessun file", "Seleziona almeno un file da convertire.")
            return
        
        # Determina directory di output
        if self.use_default_output_cb.isChecked():
            # Usa cartella 'converted' nella stessa directory del primo file
            if self.selected_files:
                first_file = Path(self.selected_files[0])
                self.output_directory = str(first_file.parent / "converted")
        elif not self.output_directory:
            QMessageBox.warning(self, "Directory mancante", "Seleziona una directory di output.")
            return
        
        # Disabilita bottone durante la conversione
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Conversione in corso...")
        
        # Ottieni opzioni
        options = self._get_conversion_options()
        
        # Crea e avvia il worker
        self.worker = ConversionWorker(
            files=self.selected_files,
            output_dir=self.output_directory,
            options=options
        )
        
        self.worker.progress.connect(self._on_progress)
        self.worker.file_complete.connect(self._on_file_complete)
        self.worker.finished.connect(self._on_conversion_finished)
        self.worker.error.connect(self._on_error)
        
        self.worker.start()
        
        self._log(f"Avviata conversione di {len(self.selected_files)} file", "info")

    def _on_progress(self, percent: int, message: str):
        """Gestisce l'aggiornamento del progresso."""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)

    def _on_file_complete(self, filename: str, success: bool, message: str):
        """Gestisce il completamento di un singolo file."""
        if success:
            self._log(f"✓ {filename}: {message}", "success")
        else:
            self._log(f"✗ {filename}: {message}", "error")

    def _on_conversion_finished(self, results: list):
        """Gestisce il completamento di tutte le conversioni."""
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("Avvia Conversione")
        
        # Conta successi ed errori
        success_count = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        self._log(f"\n=== Conversione completata: {success_count}/{total} file ===", "info")
        
        # Mostra riepilogo
        if success_count == total:
            QMessageBox.information(
                self,
                "Conversione completata",
                f"Tutti i {total} file sono stati convertiti con successo!\n\n"
                f"Output salvato in: {self.output_directory}"
            )
        elif success_count > 0:
            QMessageBox.warning(
                self,
                "Conversione parziale",
                f"{success_count}/{total} file convertiti con successo.\n"
                f"{total - success_count} file hanno fallito.\n\n"
                f"Controlla il log per i dettagli."
            )
        else:
            QMessageBox.critical(
                self,
                "Conversione fallita",
                "Nessun file è stato convertito con successo.\n\n"
                "Controlla il log per i dettagli."
            )

    def _on_error(self, error_message: str):
        """Gestisce gli errori durante la conversione."""
        self._log(f"ERRORE: {error_message}", "error")
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("Avvia Conversione")

    def _log(self, message: str, level: str = "info"):
        """Aggiunge un messaggio al log."""
        timestamp = QThread.currentThread().objectName() or "UI"
        
        if level == "success":
            color = "#4CAF50"  # Verde
        elif level == "error":
            color = "#f44336"  # Rosso
        elif level == "warning":
            color = "#ff9800"  # Arancione
        else:
            color = "#2196F3"  # Blu
        
        log_entry = f'<span style="color: {color};">[{level.upper()}]</span> {message}<br>'
        self.log_text.append(log_entry)
        
        # Scroll automatico alla fine
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
