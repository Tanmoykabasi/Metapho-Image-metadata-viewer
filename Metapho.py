import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTextBrowser, QScrollArea, 
                             QFrame, QSizePolicy, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt, QTimer
import cv2
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pillow_heif
import numpy as np
from PyQt5.QtGui import QIcon

class MetadataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metapho: Photo Metadata Viewer")
        self.setGeometry(100, 100, 1000, 700)
        
        self.setWindowIcon(QIcon(r"C:\Users\Tanmoy\Desktop\bot\icon\icon26.png"))
        # Camera variables
        self.capture_window = None
        self.cap = None
        self.timer = None
        
        # Set application-wide styles
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #F8F9FA;
                color: #212529;
            }
            QTextBrowser, QLabel {
                background-color: #FFFFFF;
                color: #212529;
                border: 1px solid #CED4DA;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #212529;
                border: 1px solid #CED4DA;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E9ECEF;
            }
            QPushButton:pressed {
                background-color: #DEE2E6;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Top panel with buttons
        button_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Photo")
        self.capture_btn = QPushButton("Capture Photo")
        self.upload_btn.clicked.connect(self.upload_photo)
        self.capture_btn.clicked.connect(self.show_camera_window)
        button_layout.addWidget(self.upload_btn)
        button_layout.addWidget(self.capture_btn)
        button_layout.addStretch()
        
        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left panel for image display
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        image_frame = QFrame()
        image_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px;")
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(10, 10, 10, 10)
        
        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("border: none; background-color: #F8F9FA;")
        
        image_layout.addWidget(self.image_label)
        left_panel.addWidget(image_frame)
        
        # Right panel for metadata display
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        metadata_frame = QFrame()
        metadata_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px;")
        metadata_layout = QVBoxLayout(metadata_frame)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        
        metadata_header = QLabel("Metadata Information")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        metadata_header.setFont(header_font)
        metadata_header.setStyleSheet("padding: 10px; border-bottom: 1px solid #E9ECEF;")
        
        self.metadata_display = QTextBrowser()
        self.metadata_display.setReadOnly(True)
        self.metadata_display.setOpenExternalLinks(True)
        self.metadata_display.setStyleSheet("border: none; padding: 10px;")
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.metadata_display)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(400)
        scroll_area.setStyleSheet("border: none;")
        
        metadata_layout.addWidget(metadata_header)
        metadata_layout.addWidget(scroll_area)
        right_panel.addWidget(metadata_frame)
        
        # Add panels to content layout
        content_layout.addLayout(left_panel, 1)
        content_layout.addLayout(right_panel, 1)
        
        # Add elements to main layout
        main_layout.addLayout(button_layout)
        main_layout.addLayout(content_layout)
        
        # Initialize HEIF support
        pillow_heif.register_heif_opener()

    def upload_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "", 
            "Image Files (*.jpg *.jpeg *.tiff *.tif *.png *.heic *.heif)"
        )
        if file_path:
            self.process_image(file_path)

    def show_camera_window(self):
        # Create camera window
        self.capture_window = QMainWindow(self)
        self.capture_window.setWindowTitle("Camera Capture")
        self.capture_window.setGeometry(200, 200, 800, 600)
        
        central_widget = QWidget()
        self.capture_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Video display label
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.camera_label)
        
        # Capture button
        capture_btn = QPushButton("Take Photo")
        capture_btn.clicked.connect(self.capture_photo)
        layout.addWidget(capture_btn)
        
        # Start camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Camera Error", "Could not access camera")
            return
            
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera_frame)
        self.timer.start(30)  # Update every 30 ms
        
        self.capture_window.show()

    def update_camera_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Convert to RGB (OpenCV uses BGR)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.camera_label.setPixmap(pixmap.scaled(
                self.camera_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))

    def capture_photo(self):
        ret, frame = self.cap.read()
        if ret:
            # Save captured image to temporary file
            temp_path = os.path.join(os.getcwd(), "captured_photo.jpg")
            cv2.imwrite(temp_path, frame)
            
            # Stop camera and close window
            self.timer.stop()
            self.cap.release()
            self.capture_window.close()
            
            # Process captured image
            self.process_image(temp_path)
            
            # Clean up temporary file after processing
            QTimer.singleShot(1000, lambda: self.remove_temp_file(temp_path))

    def remove_temp_file(self, path):
        try:
            os.remove(path)
        except:
            pass

    def process_image(self, file_path):
        try:
            # Display image
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                # Try with PIL for unsupported formats
                pil_image = Image.open(file_path)
                qimage = self.pil_to_qimage(pil_image)
                pixmap = QPixmap.fromImage(qimage)
            
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
            else:
                self.image_label.setText("Cannot display image")
            
            # Extract and display metadata
            self.extract_metadata(file_path)
            
        except Exception as e:
            self.metadata_display.setHtml(f"<html><body><p>Error processing image: {str(e)}</p></body></html>")

    def pil_to_qimage(self, pil_image):
        if pil_image.mode == "RGB":
            r, g, b = pil_image.split()
            pil_image = Image.merge("RGB", (b, g, r))
        elif pil_image.mode == "RGBA":
            r, g, b, a = pil_image.split()
            pil_image = Image.merge("RGBA", (b, g, r, a))
        elif pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(data, pil_image.size[0], pil_image.size[1], QImage.Format_RGB888)
        return qimage

    def extract_metadata(self, file_path):
        try:
            image = Image.open(file_path)
            metadata_text = "<html><body>"
            
            # EXIF Data
            exifdata = image.getexif()
            if exifdata:
                metadata_text += "<h3>EXIF Data</h3><ul>"
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exifdata.get(tag_id)
                    
                    # Handle GPS data
                    if tag == "GPSInfo":
                        gps_ifd = exifdata.get_ifd(tag_id)
                        if gps_ifd:
                            metadata_text += f"<li><b>{tag}:</b><ul>"
                            for gps_tag_id, gps_value in gps_ifd.items():
                                gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                metadata_text += f"<li><b>{gps_tag}:</b> {gps_value}</li>"
                            # Parse GPS coordinates with error handling
                            lat = gps_ifd.get(2)
                            lat_ref = gps_ifd.get(1)
                            lon = gps_ifd.get(4)
                            lon_ref = gps_ifd.get(3)
                            
                            parsed_lat = None
                            parsed_lon = None
                            
                            if lat and lat_ref and isinstance(lat, (tuple, list)) and len(lat) >= 3:
                                parsed_lat = self._dms_to_decimal(lat, lat_ref)
                                if parsed_lat is not None:
                                    metadata_text += f"<li><b>Parsed Latitude:</b> {parsed_lat:.6f}</li>"
                            if lon and lon_ref and isinstance(lon, (tuple, list)) and len(lon) >= 3:
                                parsed_lon = self._dms_to_decimal(lon, lon_ref)
                                if parsed_lon is not None:
                                    metadata_text += f"<li><b>Parsed Longitude:</b> {parsed_lon:.6f}</li>"
                            
                            # Reverse geocoding if coordinates are available
                            if parsed_lat is not None and parsed_lon is not None:
                                try:
                                    from geopy.geocoders import Nominatim
                                    geolocator = Nominatim(user_agent="photo_metadata_viewer")
                                    location = geolocator.reverse((parsed_lat, parsed_lon), language="en")
                                    if location:
                                        metadata_text += f"<li><b>Address:</b> {location.address}</li>"
                                        addr = location.raw.get('address', {})
                                        state = addr.get('state', 'Unknown')
                                        metadata_text += f"<li><b>State:</b> {state}</li>"
                                        metadata_text += f"<li><b>Google Maps Link:</b> <a href='https://www.google.com/maps/search/?api=1&query={parsed_lat},{parsed_lon}'>View on Google Maps</a></li>"
                                except ConnectionRefusedError:
                                    metadata_text += "<li><b>Geocoding Error:</b> Connection refused. Check your internet connection or try again later.</li>"
                                except ImportError:
                                    metadata_text += "<li>(Install geopy via 'pip install geopy' for address details)</li>"
                                except Exception as e:
                                    metadata_text += f"<li>Reverse geocoding error: {str(e)}</li>"
                            metadata_text += "</ul></li>"
                        else:
                            metadata_text += f"<li><b>{tag}:</b> {data}</li>"
                    else:
                        metadata_text += f"<li><b>{tag}:</b> {data}</li>"
                metadata_text += "</ul>"
            else:
                metadata_text += "<p>No EXIF data found</p>"
            
            # IPTC Data
            try:
                from iptcinfo3 import IPTCInfo
                iptc_info = IPTCInfo(file_path)
                if len(iptc_info) > 0:
                    metadata_text += "<h3>IPTC Data</h3><ul>"
                    for key in iptc_info:
                        value = iptc_info[key]
                        if isinstance(value, list):
                            value = ', '.join(map(str, value))
                        metadata_text += f"<li><b>{key}:</b> {value}</li>"
                    metadata_text += "</ul>"
                else:
                    metadata_text += "<p>No IPTC data found</p>"
            except ImportError:
                metadata_text += "<p>IPTC support not available (install iptcinfo3)</p>"
            except Exception as e:
                metadata_text += f"<p>IPTC Error: {str(e)}</p>"
            
            # XMP Data
            try:
                import xmltodict
                with open(file_path, 'rb') as f:
                    content = f.read()
                    xmp_start = content.find(b'<x:xmpmeta')
                    xmp_end = content.find(b'</x:xmpmeta>') + 12
                    
                    if xmp_start != -1 and xmp_end != -1:
                        xmp_data = content[xmp_start:xmp_end]
                        try:
                            xmp_dict = xmltodict.parse(xmp_data)
                            metadata_text += "<h3>XMP Data</h3>"
                            metadata_text += self.format_xmp_dict_html(xmp_dict, 0)
                        except Exception as e:
                            metadata_text += f"<p>XMP Parsing Error: {str(e)}</p>"
                    else:
                        metadata_text += "<p>No XMP data found</p>"
            except ImportError:
                metadata_text += "<p>XMP support not available (install xmltodict)</p>"
            except Exception as e:
                metadata_text += f"<p>XMP Error: {str(e)}</p>"
            
            # Basic file information
            metadata_text += "<h3>File Information</h3><ul style='text-align: left;'>"
            metadata_text += f"<li><b>File Name:</b> {os.path.basename(file_path)}</li>"
            metadata_text += f"<li><b>File Size:</b> {os.path.getsize(file_path)} bytes</li>"
            metadata_text += f"<li><b>Dimensions:</b> {image.size[0]} x {image.size[1]} pixels</li>"
            metadata_text += f"<li><b>Format:</b> {image.format}</li>"
            metadata_text += f"<li><b>Mode:</b> {image.mode}</li>"
            metadata_text += "</ul>"
            
            metadata_text += "</body></html>"
            
            self.metadata_display.setHtml(metadata_text)
            
        except Exception as e:
            self.metadata_display.setHtml(f"<html><body><p>Error extracting metadata: {str(e)}</p></body></html>")

    def format_xmp_dict_html(self, d, indent=0):
        result = "<ul>" if indent == 0 else ""
        for key, value in d.items():
            key_name = key.split('}')[-1] if '}' in key else key
            if isinstance(value, dict):
                result += "  " * indent + f"<li><b>{key_name}:</b>"
                result += self.format_xmp_dict_html(value, indent + 1)
                result += "</li>"
            elif isinstance(value, list):
                result += "  " * indent + f"<li><b>{key_name}:</b><ul>"
                for item in value:
                    if isinstance(item, dict):
                        result += self.format_xmp_dict_html(item, indent + 1)
                    else:
                        result += f"<li>{item}</li>"
                result += "</ul></li>"
            else:
                result += "  " * indent + f"<li><b>{key_name}:</b> {value}</li>"
        if indent == 0:
            result += "</ul>"
        return result

    def _dms_to_decimal(self, dms, ref):
        if dms is None or ref is None:
            return None
        degrees = dms[0][0] / dms[0][1] if isinstance(dms[0], tuple) else float(dms[0])
        minutes = dms[1][0] / dms[1][1] if isinstance(dms[1], tuple) else float(dms[1])
        seconds = dms[2][0] / dms[2][1] if isinstance(dms[2], tuple) else float(dms[2])
        decimal = degrees + minutes / 60 + seconds / 3600
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal

    def closeEvent(self, event):
        # Clean up camera resources if needed
        if self.cap and self.cap.isOpened():
            self.cap.release()
        if self.timer and self.timer.isActive():
            self.timer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetadataViewer()
    window.show()
    sys.exit(app.exec_())