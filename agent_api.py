from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from agents import detective_orchestrator, CaseState
from RAG.embeddings import EmbeddingService
from RAG.database import SnowflakeVectorDB
from image_generator import SurveillanceImageGenerator
import json
import os
import base64
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'tiff', 'tif', 'bmp'}

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Image output folder for surveillance frame reconstructions
IMAGE_OUTPUT_FOLDER = 'outputs/images'
if not os.path.exists(IMAGE_OUTPUT_FOLDER):
    os.makedirs(IMAGE_OUTPUT_FOLDER)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/analyze-case', methods=['POST'])
def analyze_case():
    """
    Endpoint to receive case data and invoke the LangGraph agents.

    Expected multipart form data:
    - Inc_over: Incident overview text
    - Targ: Target information
    - Phy_Evi: Physical evidence description
    - wit_test: Witness testimony
    - leads: Leads information
    - evidence_image: (Optional) Image file for RAG retrieval
    - evidence_images: (Optional) Multiple image files for video reconstruction
    """
    try:
        # Get form data (multipart/form-data for file uploads)
        data = request.form.to_dict()
        
        # Get evidence image if provided (single image for RAG)
        evidence_image_bytes = None
        if 'evidence_image' in request.files:
            file = request.files['evidence_image']
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    # Read image bytes directly into memory
                    evidence_image_bytes = file.read()
                    print(f"✅ Evidence image received: {len(evidence_image_bytes)} bytes")
                except Exception as e:
                    print(f"⚠️  Error reading evidence image: {str(e)}")
        
        # Get multiple evidence images for video reconstruction
        evidence_images_for_video = []
        saved_image_paths = []
        if 'evidence_images' in request.files:
            files = request.files.getlist('evidence_images')
            for i, file in enumerate(files):
                if file and file.filename != '' and allowed_file(file.filename):
                    try:
                        image_bytes = file.read()
                        evidence_images_for_video.append(image_bytes)
                        # Save to disk for Sora to use
                        filename = secure_filename(f"video_evidence_{i}_{file.filename}")
                        filepath = os.path.join(UPLOAD_FOLDER, filename)
                        with open(filepath, 'wb') as f:
                            f.write(image_bytes)
                        saved_image_paths.append(filepath)
                        print(f"✅ Video evidence image {i+1} saved: {filepath}")
                    except Exception as e:
                        print(f"⚠️  Error reading evidence image {i}: {str(e)}")

        # Validate required fields
        required_fields = ['Inc_over', 'Targ', 'Phy_Evi', 'wit_test', 'leads']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Prepare the initial case state
        initial_state = {
            'Inc_over': data['Inc_over'],
            'Targ': data['Targ'],
            'Phy_Evi': data['Phy_Evi'],
            'wit_test': data['wit_test'],
            'leads': data['leads'],
            'agent_reports': [],  # Will be populated by agents
            'evidence_image': evidence_image_bytes  # Add image bytes for RAG
        }

        print(f"\n🔍 Processing case analysis...")
        print(f"Incident: {data['Inc_over'][:100]}...")
        if evidence_image_bytes:
            print(f"🖼️  RAG retrieval enabled with evidence image")

        # Invoke the detective orchestrator
        result = detective_orchestrator.invoke(initial_state)

        # Extract all agent reports
        agent_reports = result.get('agent_reports', [])

        # Generate concluding report
        concluding_report = generate_concluding_report(
            initial_state,
            agent_reports
        )

        print(f"✅ Analysis complete - {len(agent_reports)} reports generated")

        # Remove non-JSON-serializable fields (e.g., raw bytes) from case_state
        safe_case_state = dict(result) if isinstance(result, dict) else {}
        if 'evidence_image' in safe_case_state:
            # Drop raw bytes from the response to avoid serialization issues
            safe_case_state.pop('evidence_image', None)

        # Generate video reconstruction if images are available
        video_reconstruction = None
        if saved_image_paths or evidence_image_bytes:
            video_reconstruction = generate_video_reconstruction(
                concluding_report,
                saved_image_paths if saved_image_paths else None,
                evidence_image_bytes if not saved_image_paths else None
            )

        response_data = {
            'success': True,
            'agent_reports': agent_reports,
            'concluding_report': concluding_report,
            'case_state': safe_case_state
        }
        
        if video_reconstruction:
            response_data['video_reconstruction'] = video_reconstruction

        return jsonify(response_data)

    except Exception as e:
        print(f"❌ Error processing case: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def generate_concluding_report(initial_state, agent_reports):
    """
    Generate a final concluding report based on all agent findings.
    """
    report_sections = []

    # Header
    report_sections.append("=" * 80)
    report_sections.append("DETECTIVE CASE ANALYSIS - CONCLUDING REPORT")
    report_sections.append("=" * 80)
    report_sections.append("")

    # Case Overview
    report_sections.append("📋 CASE OVERVIEW:")
    report_sections.append(initial_state['Inc_over'])
    report_sections.append("")

    # Target Information
    report_sections.append("🎯 TARGET(S):")
    report_sections.append(initial_state['Targ'])
    report_sections.append("")

    # Agent Findings
    report_sections.append("=" * 80)
    report_sections.append("SPECIALIST ANALYSIS REPORTS")
    report_sections.append("=" * 80)
    report_sections.append("")

    for i, report in enumerate(agent_reports, 1):
        report_sections.append(f"Report {i}:")
        report_sections.append("-" * 80)
        report_sections.append(report)
        report_sections.append("")

    # Summary
    report_sections.append("=" * 80)
    report_sections.append("INVESTIGATION SUMMARY")
    report_sections.append("=" * 80)
    report_sections.append("")
    report_sections.append(f"📊 Total Specialist Reports: {len(agent_reports)}")
    report_sections.append(f"🔍 Physical Evidence Analyzed: Yes" if initial_state['Phy_Evi'] else "No")
    report_sections.append(f"👥 Witness Testimony Reviewed: Yes" if initial_state['wit_test'] else "No")
    report_sections.append(f"🔗 Leads Identified: Yes" if initial_state['leads'] else "No")
    report_sections.append("")
    report_sections.append("=" * 80)
    report_sections.append("END OF REPORT")
    report_sections.append("=" * 80)

    return "\n".join(report_sections)


def generate_video_reconstruction(concluding_report, image_paths=None, single_image_bytes=None):
    """
    Generate surveillance footage reconstruction using DALL-E images.
    Creates 5 sequential frames styled as 1990s CCTV footage.
    
    Args:
        concluding_report: The full concluding report text
        image_paths: List of saved image file paths (not used for surveillance generation)
        single_image_bytes: Single image bytes (not used for surveillance generation)
        
    Returns:
        Dictionary with image reconstruction results
    """
    try:
        print("\n🎬 Starting surveillance footage reconstruction...")
        
        # Check if OpenAI API key is configured
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️ OPENAI_API_KEY not set - skipping reconstruction")
            return {
                "status": "skipped",
                "message": "Reconstruction requires OPENAI_API_KEY",
                "type": "images",
                "frames": []
            }
        
        # Generate surveillance frames using DALL-E
        generator = SurveillanceImageGenerator(output_dir=IMAGE_OUTPUT_FOLDER)
        result = generator.generate_frames(concluding_report)
        
        # Convert local paths to URLs for frontend
        if result.get("images"):
            for img in result["images"]:
                if img.get("path"):
                    # Convert path to URL
                    filename = os.path.basename(img["path"])
                    img["url"] = f"/outputs/images/{filename}"
        
        result["type"] = "images"
        result["frames"] = result.pop("images", [])
        
        print(f"✅ Surveillance reconstruction complete: {result.get('status')}")
        return result
        
    except Exception as e:
        print(f"❌ Reconstruction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "failed",
            "message": str(e),
            "type": "images",
            "frames": []
        }


@app.route('/api/upload-footprint', methods=['POST'])
def upload_footprint():
    """
    Endpoint to upload footprint evidence to the database.
    
    Expected multipart form data:
    - image: Footprint image file
    - id_number: ID in format XXX_YY (e.g., 001_02)
    - gender: M or W
    - brand: Shoe brand
    - model_details: Shoe model or other details
    - size: Shoe size in cm (float)
    """
    try:
        # Validate image file
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        file = request.files['image']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid image file'
            }), 400
        
        # Get form data
        id_number = request.form.get('id_number', '').strip()
        gender = request.form.get('gender', '').strip()
        brand = request.form.get('brand', '').strip()
        model_details = request.form.get('model_details', '').strip()
        size = request.form.get('size', '').strip()
        
        # Validate required fields
        if not id_number or not gender or not size:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: id_number, gender, or size'
            }), 400
        
        # Validate ID format (XXX_YY)
        import re
        if not re.match(r'^\d{3}_\d{2}$', id_number):
            return jsonify({
                'success': False,
                'error': 'ID number must be in format XXX_YY (e.g., 001_02)'
            }), 400
        
        # Validate gender
        if gender not in ['M', 'W']:
            return jsonify({
                'success': False,
                'error': 'Gender must be M or W'
            }), 400
        
        # Validate size
        try:
            size_float = float(size)
            if size_float <= 0:
                raise ValueError("Size must be positive")
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Size must be a valid positive number'
            }), 400
        
        # Read image bytes
        image_data = file.read()
        print(f"📸 Footprint image uploaded: {len(image_data)} bytes")
        
        # Save image to uploads folder
        filename = secure_filename(f"{id_number}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        print(f"💾 Image saved to: {filepath}")
        
        # Generate embedding using EmbeddingService
        print("🔄 Generating image embedding...")
        embedding_service = EmbeddingService()
        
        # Use local embeddings by default to match 512-dimension database
        embedding = embedding_service.generate_embedding(
            image_data,
            use_snowflake=False,  # Use local to ensure 512 dimensions
            preprocess=True
        )
        print(f"✅ Embedding generated: {len(embedding)} dimensions")
        
        # Prepare metadata
        metadata = {
            'id_number': id_number,
            'gender': gender,
            'brand': brand,
            'model_details': model_details,
            'size': size_float,
            'filename': filename,
            'image_path': filepath
        }
        
        # Insert into Snowflake database
        print("📤 Uploading to Snowflake database...")
        db = SnowflakeVectorDB()
        
        db.insert_record(
            id=id_number,
            image_path=filepath,
            metadata=metadata,
            embedding=embedding
        )
        
        print(f"✅ Footprint {id_number} successfully uploaded to database")
        
        # Clean up connections
        embedding_service.close()
        db.disconnect()
        
        return jsonify({
            'success': True,
            'message': f'Footprint evidence {id_number} uploaded successfully',
            'data': {
                'id': id_number,
                'metadata': metadata,
                'embedding_dimensions': len(embedding)
            }
        })
    
    except Exception as e:
        print(f"❌ Error uploading footprint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to upload footprint: {str(e)}'
        }), 500


@app.route('/outputs/images/<path:filename>')
def serve_image(filename):
    """Serve generated surveillance images"""
    return send_from_directory(IMAGE_OUTPUT_FOLDER, filename)


@app.route('/api/generate-reconstruction', methods=['POST'])
def generate_reconstruction_standalone():
    """
    Generate surveillance reconstruction from hardcoded demo files.
    Uses message.txt as the police report.
    
    In the future, this will be connected to uploaded case files.
    """
    try:
        print("\n🎬 Starting standalone surveillance reconstruction...")
        
        # Check if OpenAI API key is configured
        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({
                "success": False,
                "error": "OPENAI_API_KEY not set. Please configure it in your .env file."
            }), 400
        
        # Use hardcoded demo file
        report_path = Path("footwear_rag/data/zip_files/message.txt")
        
        if not report_path.exists():
            return jsonify({
                "success": False,
                "error": f"Demo report file not found: {report_path}"
            }), 404
        
        # Read the report
        with open(report_path, 'r', encoding='utf-8') as f:
            report_text = f.read()
        
        print(f"📄 Loaded report: {len(report_text)} characters")
        
        # Generate surveillance frames
        generator = SurveillanceImageGenerator(output_dir=IMAGE_OUTPUT_FOLDER)
        result = generator.generate_frames(report_text)
        
        # Convert local paths to URLs for frontend
        if result.get("images"):
            for img in result["images"]:
                if img.get("path"):
                    filename = os.path.basename(img["path"])
                    img["url"] = f"/outputs/images/{filename}"
        
        # Restructure response
        response_data = {
            "success": True,
            "data": {
                "status": result.get("status", "failed"),
                "total": result.get("total", 0),
                "completed": result.get("completed", 0),
                "failed": result.get("failed", 0),
                "frames": result.get("images", [])
            }
        }
        
        print(f"✅ Reconstruction complete: {result.get('completed', 0)}/{result.get('total', 0)} frames")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Reconstruction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Detective Agent API'})


if __name__ == '__main__':
    print("\n🤖 Detective Agent API Server Starting...")
    print("🔗 API will be available at http://localhost:5000")
    print("📡 Endpoint: POST /api/analyze-case")
    print("━" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
