from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from backend.db_helper import *
from main import *
import os
import json

app = Flask(__name__)
app.secret_key = 'quizo_secret_2024'
CORS(app)

@app.route('/signup_data', methods=['POST'])
def signup_data():
    data = request.get_json()
    if insert_signup(data['signupEmail'], data['username'], data['signupPassword']) == 1:
        return jsonify({'message': 'Data inserted successfully!'})
    return jsonify({'message': 'Error in inserting the Data!'})

@app.route('/login_data', methods=['POST'])
def login_data():
    data = request.get_json()
    print(data)
    response_data = search_login_credentials(data['email'], data['password'])
    if response_data:
        session['user_email'] = data['email']
        return jsonify(response_data)
    return jsonify({'message': 'Data not found!'})

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/create_exam')
def create_exam_page():
    return render_template('create_exam.html')

@app.route('/create_exam_data', methods=['POST'])
def create_exam_data():
    data = request.get_json()
    email = session.get('user_email', 'unknown')
    questions_json = json.dumps(data['questions'], ensure_ascii=False)
    exam_id = create_exam(data['title'], data['password'], questions_json, data['duration'], email)
    if exam_id:
        return jsonify({'success': True, 'exam_id': exam_id})
    return jsonify({'success': False, 'message': 'خطأ في إنشاء الامتحان'})

@app.route('/join_exam')
def join_exam_page():
    return render_template('join_exam.html')

@app.route('/join_exam_data', methods=['POST'])
def join_exam_data():
    data = request.get_json()
    exam = get_exam_by_password(data['password'])
    if exam:
        session['current_exam_id'] = exam['id']
        session['student_name'] = data.get('student_name', 'غير معروف')
        return jsonify({'success': True, 'exam_id': exam['id']})
    return jsonify({'success': False, 'message': 'كلمة السر غير صحيحة'})

@app.route('/exam_data/<int:exam_id>')
def exam_data(exam_id):
    try:
        exam = get_exam_by_id(exam_id)
        print(f'[exam_data] id={exam_id}, found={exam is not None}')
        if not exam:
            return jsonify({'error': 'الامتحان غير موجود'}), 404

        q = exam['questions']
        print(f'[exam_data] questions type={type(q).__name__}, value={str(q)[:120]}')
        if isinstance(q, (bytes, bytearray)):
            q = json.loads(q.decode('utf-8'))
        elif isinstance(q, str):
            q = json.loads(q)
        # else already list/dict

        return jsonify({
            'title':     exam['title'],
            'duration':  exam['duration'],
            'questions': q
        })
    except Exception as e:
        print(f'[exam_data] ERROR: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/my_exams')
def my_exams():
    email = session.get('user_email', '')
    exams = get_exams_by_user(email) if email else []
    for e in exams:
        if hasattr(e.get('created_at'), 'strftime'):
            e['created_at'] = e['created_at'].strftime('%Y-%m-%d %H:%M')
    return jsonify(exams)

@app.route('/quiz_html')
def quiz_page():
    exam_id = request.args.get('exam_id') or session.get('current_exam_id')
    student_name = session.get('student_name', '')
    return render_template('quiz.html', exam_id=exam_id, student_name=student_name)

@app.route('/submit_result', methods=['POST'])
def submit_result():
    data = request.get_json()
    exam_id      = data.get('exam_id')
    student_name = data.get('student_name', session.get('student_name', 'غير معروف'))
    score        = data.get('score', 0)
    total        = data.get('total', 0)
    violations   = data.get('violations', 0)
    cheat_events = json.dumps(data.get('cheat_events', []), ensure_ascii=False)
    ok = save_exam_result(exam_id, student_name, score, total, violations, cheat_events)
    return jsonify({'success': ok})

@app.route('/exam_analytics/<int:exam_id>')
def exam_analytics(exam_id):
    exam = get_exam_by_id(exam_id)
    if not exam:
        return 'الامتحان غير موجود', 404
    return render_template('exam_analytics.html', exam_id=exam_id, exam_title=exam['title'])

@app.route('/exam_results_data/<int:exam_id>')
def exam_results_data(exam_id):
    results = get_exam_results(exam_id)
    out = []
    for r in results:
        ce = r['cheat_events']
        if isinstance(ce, (bytes, bytearray)):
            ce = json.loads(ce.decode('utf-8'))
        elif isinstance(ce, str):
            ce = json.loads(ce)
        out.append({
            'student_name': r['student_name'],
            'score':        r['score'],
            'total':        r['total'],
            'violations':   r['violations'],
            'cheat_events': ce or [],
            'submitted_at': r['submitted_at'].strftime('%Y-%m-%d %H:%M') if hasattr(r['submitted_at'], 'strftime') else str(r['submitted_at'])
        })
    return jsonify(out)

# ✅ هاد الراوت يبعث فريمات الكاميرا للمتصفح
@app.route('/video_feed')
def video_feed():
    return Response(proctoringAlgo(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/proctoring_data')
def proctoring_data():
    """يرجع أحداث الغش + حالة الكشف الحالية في طلب واحد."""
    import main
    with main.cheat_events_lock:
        events = list(main.cheat_events_queue)
        main.cheat_events_queue.clear()
    with main.detection_state_lock:
        state = dict(main.detection_state)
    return jsonify({"events": events, "status": state})

@app.route('/stop_camera')
def stop_camera():
    global running
    running = False
    main_app()
    print('Camera and Server stopping.....')
    os._exit(0)

if __name__ == "__main__":
    print("Starting the Python Flask Server.....")
    app.run(port=5000, debug=False)  # ✅ debug=False عشان ما تفتح الكاميرا مرتين