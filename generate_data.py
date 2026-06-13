import requests
import random

# 定义一些基础数据，模拟班级情况
subjects = ["Python", "Math", "Physics", "Chemistry"]
intents = ["Provider", "Receiver"]
# 为了演示，我们将 advantage/weakness 简化，方便算法匹配
skills = ["Coding", "Algebra", "Calculus", "Physics", "Design"]

def generate_and_add():
    for i in range(10):
        # 随机生成用户数据
        user = {
            "name": f"Student_{i+1}",
            "subject_id": random.choice(subjects),
            "time_slots": "MON_1,WED_3",
            "advantage": random.choice(skills),
            "weakness": random.choice(skills),
            "intent": random.choice(intents),
            "fee_pref": "Free Only",
            "role": "Student (Peer)",
            "privacy_mode": False,
            "rating": round(random.uniform(3.0, 5.0), 1)
        }
        
        # 发送请求到你本地的 API
        try:
            response = requests.post("http://127.0.0.1:5000/api/add_user", json=user)
            print(f"Added {user['name']}: {response.status_code}")
        except Exception as e:
            print(f"Error adding {user['name']}: {e}")

if __name__ == "__main__":
    generate_and_add()
    print("完成！10 个虚拟同学已存入数据库。")