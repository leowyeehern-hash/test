import pandas as pd  # 1. 顶部导入
from flask import Flask, request, jsonify
from database import create_table, get_users, save_or_update_user,connect

app = Flask(__name__)

# 初始化数据库
create_table()

# --- 1. 你的核心算法 (保持原样放在这里) ---
def calculate_match(s1, s2):
    # 使用 .get() 安全地获取数据，如果找不到，给一个默认值防止崩溃
    sub1 = str(s1.get('subject_id', '')).strip().upper()
    sub2 = str(s2.get('subject_id', '')).strip().upper()
    
    if sub1 != sub2:
        return 0, []

    score = 0
    reasons = []
    
    i1 = s1.get('intent', 'Unknown')
    i2 = s2.get('intent', 'Unknown')
    f1 = s1.get('fee_pref', 'Unknown')
    f2 = s2.get('fee_pref', 'Unknown')

    is_study_buddy_pair = False
    
    if i1 == 'Provider' and i2 == 'Provider':
        return 0, []
        
    elif i1 == 'Receiver' and i2 == 'Receiver':
        if f1 == 'Free Only' and f2 == 'Free Only':
            is_study_buddy_pair = True
            score += 35
            reasons.append("📚 Study Buddy Match: Both seeking peers! (+35)")
        else:
            return 0, []
    else:
        receiver_fee = f1 if i1 == 'Receiver' else f2
        provider_fee = f1 if i1 == 'Provider' else f2
        
        if receiver_fee == 'Free Only' and provider_fee == 'Paid Only':
            return 0, []
        elif receiver_fee == 'Free Only' and provider_fee == 'Free Only':
            score += 20
            reasons.append("🌱 Voluntarism Match: Free connection! (+20)")
        elif receiver_fee == 'Paid Only':
            score += 15
            reasons.append("💰 Premium Match: Paid Receiver (+15)")
            if provider_fee == 'Paid Only':
                score += 10
                reasons.append("🤝 Premium Deal: Paid Tutor (+10)")

    # 技能和时间槽处理 (同样使用 .get)
    s1_adv = [x.strip().lower() for x in str(s1.get('advantage', '')).split(",") if x.strip()]
    s1_weak = [x.strip().lower() for x in str(s1.get('weakness', '')).split(",") if x.strip()]
    s2_adv = [x.strip().lower() for x in str(s2.get('advantage', '')).split(",") if x.strip()]
    s2_weak = [x.strip().lower() for x in str(s2.get('weakness', '')).split(",") if x.strip()]
    
    def check_complementary(adv_list, weak_list):
        for adv in adv_list:
            for weak in weak_list:
                if adv in weak or weak in adv: return True
        return False

    is_complementary = (i1 == 'Provider' and check_complementary(s1_adv, s2_weak)) or \
                       (i2 == 'Provider' and check_complementary(s2_adv, s1_weak))

    has_shared_strength = False
    for adv1 in s1_adv:
        for adv2 in s2_adv:
            if adv1 in adv2 or adv2 in adv1:
                has_shared_strength = True
                break

    if is_study_buddy_pair:
        if has_shared_strength:
            score += 20
            reasons.append("🤝 Buddy Synergy (+20)")
    else:
        if is_complementary and has_shared_strength:
            score += 55
            reasons.append("⚡ Ultimate Match (+55)")
        elif is_complementary:
            score += 45
            reasons.append("✓ Complementary Match (+45)")
        elif has_shared_strength:
            score += 25
            reasons.append("🤝 Shared Stack (+25)")
        else:
            score -= 10
            reasons.append("⚠ Skill Gap (-10)")

    # 软性习惯匹配 (这里是之前报错的重灾区)
    fields = ['frequency', 'study_mode', 'group_size', 'grade_goal', 'study_style', 'resource_pref', 'language']
    matched_fields = []
    for field in fields:
        # 核心改动：使用 .get() 给所有可能缺失的字段默认值
        val1 = str(s1.get(field, 'Unknown')).strip().lower()
        val2 = str(s2.get(field, 'Unknown')).strip().lower()
        if val1 != 'unknown' and val1 == val2:
            score += 2
            matched_fields.append(field.replace("_", " ").title())
    if matched_fields:
        reasons.append(f"✓ Shared Habits ({', '.join(matched_fields)}) (+{len(matched_fields)*2})")

    # 身份和评分
    r1 = s1.get('role', 'Unknown')
    r2 = s2.get('role', 'Unknown')
    if r1 == 'Student (Peer)' and r2 == 'Student (Peer)': score += 5
    elif r1 == 'Alumni (Mentor)' and r2 == 'Alumni (Mentor)': score += 5

    user_rating = float(s2.get('rating', 3.0))
    if user_rating >= 4.5:
        score += 10
        reasons.append(f"★ Top-Rated Peer (+10)")
    elif user_rating < 3.0:
        score -= 15
        reasons.append(f"⚠ Low Peer Rating (-15)")

    return max(0, min(score, 100)), reasons

# --- 2. 匹配接口 (缝合数据库与算法) ---
@app.route('/api/match', methods=['POST'])
def match_api():
    # --- 放在这里：直接在接收数据后立刻检查 ---
    if 'user_info' not in request.json:
        return jsonify({"error": "缺少 user_info"}), 400
    if 'name' not in request.json['user_info']:
        return jsonify({"error": "缺少 name"}), 400
    # ------------------------------------

    user_data = request.json['user_info']
    
    # 【新增】给当前用户数据补充默认值，防止报错
    required_fields = ['intent', 'fee_pref', 'role', 'rating', 'advantage', 'weakness', 'time_slots']
    for field in required_fields:
        if field not in user_data:
            user_data[field] = "Unknown" if field != 'rating' else 3.0

    all_students = get_users() 
    # ... 后续逻辑 ...
    
    match_results = []
    # 定义所有可能用到的字段列表
    all_fields = ['frequency', 'study_mode', 'group_size', 'grade_goal', 'study_style', 'resource_pref', 'language']
    
    for target in all_students:
        # 1. 强制补齐字段，确保不会触发 KeyError
        for field in all_fields:
            if field not in target or target[field] is None:
                target[field] = "Unknown"
        
        # 跳过自己
        if target.get('name') == user_data.get('name'):
            continue
            
        # 调用算法
        score, reasons = calculate_match(user_data, target)
        
        if score > 0:
            match_results.append({
                'target': target,
                'score': score,
                'reasons': reasons
            })
    
    # ...后面代码保持不变...
    match_results.sort(key=lambda x: x['score'], reverse=True)
    # ...
    
    # 隐私保护逻辑
    for res in match_results:
        # 1. 查询数据库，看当前请求用户(user_data['name']) 和 对方(res['target']['name']) 是否已匹配
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM matches WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)", 
                       (user_data['name'], res['target']['name'], res['target']['name'], user_data['name']))
        status_row = cursor.fetchone()
        conn.close()
        
        is_matched = (status_row and status_row[0] == 'matched')
        
        # 2. 如果没匹配且开启了隐私，则隐藏；如果已经匹配，则显示
        if res['target'].get('privacy_mode', False) and not is_matched:
            res['target']['contact'] = "HIDDEN"
        else:
            # 无论是否隐私，只要 matched 了就显示，或者隐私关闭也显示
            res['target']['contact'] = res['target'].get('contact_info', "No contact provided")
            
    return jsonify(match_results)

# --- 3. 添加用户接口 (调用你的 save_or_update) ---
@app.route('/api/add_user', methods=['POST'])
def add_user():
    data = request.json
    
    # 【兼容处理】如果数据包裹在 'user_info' 里，先提取出来
    if 'user_info' in data:
        data = data['user_info']
        
    # 现在这里无论如何都会从 data 中读取字段
    try:
        save_or_update_user(
            data['name'], 
            data['subject_id'], 
            data['time_slots'], 
            data['advantage'], 
            data['weakness'], 
            data['intent'], 
            data['fee_pref'], 
            data['role'], 
            data['privacy_mode'], 
            data.get('rating', 3.0) # 使用 .get 防止 rating 缺失导致的 KeyError
        )
        return jsonify({"message": "User saved successfully"})
    except KeyError as e:
        return jsonify({"error": f"缺少必要的字段: {str(e)}"}), 400

# 4. 发送消息接口
@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json
    # 检查双方是否已匹配
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM matches WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)", 
                   (data['sender'], data['receiver'], data['receiver'], data['sender']))
    res = cursor.fetchone()
    
    if not res or res[0] != 'matched':
        return jsonify({"error": "Chat unavailable: You are not yet matched."}), 403

    cursor.execute("INSERT INTO messages (sender, receiver, content) VALUES (?, ?, ?)", 
                   (data['sender'], data['receiver'], data['content']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Message sent successfully."})

# 5. 获取消息接口
@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    u1 = request.args.get('user1')
    u2 = request.args.get('user2')
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT sender, content, timestamp FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp ASC", 
                   (u1, u2, u2, u1))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"sender": r[0], "content": r[1], "time": r[2]} for r in rows])
# 2. 在 app.py 底部加入这个数据分析接口
@app.route('/api/stats', methods=['GET'])
def get_stats():
    # 从数据库获取原始数据
    users_list = get_users() 
    if not users_list:
        return jsonify({"message": "No users in database yet"})
            
    # 将列表转换为 Pandas DataFrame，这是数据处理的核心
    df = pd.DataFrame(users_list)
    
    # 统计数据：例如统计每个科目的用户人数
    subject_counts = df['subject_id'].value_counts().to_dict()
    
    # 统计数据：计算平均分（如果数据库里有 rating 字段）
    avg_rating = df['rating'].mean() if 'rating' in df.columns else 0
    
    return jsonify({
        "total_users": len(df),
        "subject_distribution": subject_counts,
        "average_rating": round(float(avg_rating), 2)
    })

@app.route('/api/confirm_match', methods=['POST'])
def confirm_match():
    data = request.json
    me, target = data['my_name'], data['target_name']
    
    conn = connect()
    cursor = conn.cursor()
    
    # 1. 先进行双向查询，看看是否已经存在任何匹配记录
    cursor.execute("SELECT status FROM matches WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)", 
                   (target, me, me, target))
    res = cursor.fetchone()
    
    # 2. 如果之前有人发过请求，且对方点确认，则升级为 matched
    if res and res[0] == 'pending':
        cursor.execute("UPDATE matches SET status='matched' WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)", 
                       (target, me, me, target))
        msg = "Match successful!"
        
    # 3. 如果没记录，则执行插入（使用你刚才优化的防重复逻辑）
    else:
        # 这里进行更严谨的判断
        cursor.execute("SELECT status FROM matches WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)", 
                       (me, target, target, me))
        existing = cursor.fetchone()
        
        if not existing:
            cursor.execute("INSERT INTO matches (user_a, user_b, status) VALUES (?, ?, 'pending')", (me, target))
            msg = "Request sent."
        elif existing[0] == 'matched':
            msg = "You are already matched."
        else:
            msg = "Request already sent; please wait for confirmation."
            
    conn.commit()
    conn.close()
    return jsonify({"message": msg})
if __name__ == '__main__':
    app.run(debug=True)