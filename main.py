import requests
import time
import json
import os

def save_creds(creds, path='instagram_creds.json'):
    with open(path, 'w') as f:
        json.dump(creds, f)

def load_creds(path='instagram_creds.json'):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def prompt_credentials():
    print("Enter your username or Instagram email:")
    username = input().strip()
    password = input("Enter your Instagram password: ").strip()
    return {'username': username, 'password': password}

def login(session, username, password):
    url_login = "https://i.instagram.com/api/v1/accounts/login/"
    timestamp = int(time.time())
    enc_password = f"#PWD_INSTAGRAM:0:{timestamp}:{password}"
    session.headers.update({
        "User-Agent": "Instagram 273.0.0.16.97 Android (30/11; 420dpi; 1080x1920; ...)",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept-Language": "en-US",
    })
    session.get("https://www.instagram.com/accounts/login/")
    data = {
        'username': username,
        'enc_password': enc_password,
        'device_id': 'android-{}'.format(os.urandom(8).hex()),
        '_csrftoken': session.cookies.get('csrftoken',''),
        'login_attempt_count': '0'
    }
    resp = session.post(url_login, data=data)
    return resp.json()

def two_factor_login(session, username, two_factor_identifier):
    code = input("Introdu codul 2FA primit: ").strip()
    url_2fa = "https://i.instagram.com/api/v1/accounts/two_factor_login/"
    data = {
        "username": username,
        "verification_code": code,
        "two_factor_identifier": two_factor_identifier,
        "trust_this_device": "1",
        "query_params": "{}",
        "identifier": "",
    }
    headers = {
        "User-Agent": session.headers.get("User-Agent"),
        "X-CSRFToken": session.cookies.get("csrftoken", ""),
    }
    resp = session.post(url_2fa, data=data, headers=headers)
    return resp.json()

def list_groups(session):
    url = 'https://i.instagram.com/api/v1/direct_v2/inbox/'
    resp = session.get(url)
    threads = resp.json().get('inbox', {}).get('threads', [])
    groups = []
    for t in threads:
        name = t.get('thread_title') or ','.join([u['username'] for u in t.get('users', [])])
        groups.append({'id': t['thread_id'], 'name': name})
    return groups

def send_message(session, thread_id, text):
    url = f"https://i.instagram.com/api/v1/direct_v2/threads/{thread_id}/items/"
    data = {
        'action': 'send_item',
        'text': text,
    }
    session.headers.update({ 'X-CSRFToken': session.cookies.get('csrftoken','') })
    return session.post(url, data=data)

def upload_photo(session, photo_path):
    upload_id = str(int(time.time() * 1000))
    url_upload = f"https://i.instagram.com/rupload_igphoto/{upload_id}_0_0"
    with open(photo_path, 'rb') as f:
        photo_data = f.read()
    headers = {
        "User-Agent": session.headers.get("User-Agent"),
        "X-Entity-Type": "image/jpeg",
        "Offset": "0",
        "X-Instagram-Rupload-Params": json.dumps({
            "upload_id": upload_id,
            "media_type": "1",
            "upload_media_width": 1080,
            "upload_media_height": 1080
        }),
        "Content-Type": "application/octet-stream",
        "X-Entity-Name": f"{upload_id}_0_0_1080_1080",
        "X-Entity-Length": str(len(photo_data)),
        "X-CSRFToken": session.cookies.get('csrftoken', ''),
    }
    response = session.post(url_upload, headers=headers, data=photo_data)
    return upload_id if response.status_code == 200 else None

def send_photo(session, thread_id, photo_path):
    upload_id = upload_photo(session, photo_path)
    if not upload_id:
        print("Eroare upload foto.")
        return
    url_send = f"https://i.instagram.com/api/v1/direct_v2/threads/{thread_id}/items/"
    data = {
        "action": "send_item",
        "item_type": "media_share",
        "media_type": "photo",
        "upload_id": upload_id,
    }
    session.headers.update({ "X-CSRFToken": session.cookies.get('csrftoken','') })
    return session.post(url_send, data=data)

def wait_for_connection():
    while True:
        try:
            requests.get("https://www.google.com", timeout=3)
            print("🔌 Conexiunea a revenit.")
            break
        except:
            print("❌ Conexiunea a fost pierdută. Aștept reconectarea...")
            time.sleep(5)

def main():
    creds = load_creds()
    if creds:
        print(f"Contul salvat este {creds['username']}? (da/nu)")
        if input().lower() == 'da':
            username, password = creds['username'], creds['password']
        else:
            creds = prompt_credentials()
            save_creds(creds)
            username, password = creds['username'], creds['password']
    else:
        creds = prompt_credentials()
        save_creds(creds)
        username, password = creds['username'], creds['password']

    session = requests.Session()
    login_resp = login(session, username, password)

    if login_resp.get('two_factor_required'):
        tfa_id = login_resp['two_factor_info']['two_factor_identifier']
        print("🔐 2FA necesar. Introdu codul.")
        login_resp = two_factor_login(session, username, tfa_id)

    if login_resp.get('status') != 'ok':
        print("❌ Login eșuat:", login_resp)
        return

    print("✅ Login successful!")

    print("Ce vrei sa trimiti? (mesaje spam/poze)")
    choice = input().strip().lower()
    if choice == 'mesaje spam':
        print("Enter your text path here:")
        text_path = input().strip()
        with open(text_path) as f:
            texts = [line.strip() for line in f if line.strip()]
        send_func = lambda tid, msg: send_message(session, tid, msg)
    elif choice == 'poze':
        print("Enter your photo path here:")
        photo_path = input().strip()
        send_func = lambda tid, _: send_photo(session, tid, photo_path)
    else:
        print("Opțiune invalidă.")
        return

    print("Unde vrei sa trimiti? (utilizatori/grupuri)")
    dest = input().strip().lower()
    targets = []
    if dest == 'utilizatori':
        print("Introdu numele utilizatorilor cu virgule:")
        names = [u.strip() for u in input().split(',')]
        for u in names:
            try:
                res = session.get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={u}")
                user_id = res.json()['data']['user']['pk_id']
                thread_id = start_thread(session, user_id)
                targets.append(thread_id)
            except:
                print(f"❌ Nu s-a putut obține ID pentru {u}")
    elif dest == 'grupuri':
        groups = list_groups(session)
        for i, g in enumerate(groups, 1):
            print(f"{i}. {g['name']}")
        print("Selectează grupurile (numere, separate cu virgulă):")
        picks = [int(x.strip()) - 1 for x in input().split(',')]
        for idx in picks:
            targets.append(groups[idx]['id'])
    else:
        print("Opțiune invalidă.")
        return

    print("Introdu delayul între mesaje (în secunde):")
    delay = float(input().strip())

    print("🚀 Începem trimiterea...")
    while True:
        for tid in targets:
            for text in (texts if choice == 'mesaje spam' else ['']):
                try:
                    resp = send_func(tid, text)
                    if resp is not None:
                        print(f"✅ Trimis către {tid}: {resp.status_code}")
                    time.sleep(delay)
                except Exception as e:
                    print("⚠️ Eroare la trimitere:", e)
                    wait_for_connection()

def start_thread(session, user_id):
    url = "https://i.instagram.com/api/v1/direct_v2/create_group_thread/"
    data = {
        "recipient_users": json.dumps([[str(user_id)]]),
        "client_context": str(int(time.time() * 1000)),
        "action": "create_group"
    }
    session.headers.update({"X-CSRFToken": session.cookies.get('csrftoken', '')})
    resp = session.post(url, data=data)
    if resp.status_code == 200:
        return resp.json()['thread_id']
    else:
        raise Exception("Eroare creare thread nou.")

if __name__ == '__main__':
    main()
