import requests
import time


def get_all_generate_models(api_key):
    """Lấy tất cả các model có hỗ trợ generateContent của API Key này."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None, f"Không lấy được danh sách model (HTTP {response.status_code})"

        data = response.json()
        models = []
        for model in data.get("models", []):
            methods = model.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                # Lấy tên dạng "models/gemini-1.5-flash"
                models.append(model["name"])
        return models, "OK"
    except Exception as e:
        return None, f"Lỗi kết nối: {str(e)[:80]}"


def test_model(key, model_full_name):
    """Gửi câu hỏi 'hello' tới model cụ thể."""
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_full_name}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": "hello"}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        status_code = response.status_code

        if status_code == 200:
            return "SUCCESS", "OK (200)"
        else:
            try:
                err_data = response.json()
                err_msg = err_data.get("error", {}).get("message", response.text)
                short_msg = err_msg.replace("\n", " ")[:100] + "..."
            except:
                short_msg = response.text[:100]
            return f"FAIL ({status_code})", short_msg

    except requests.exceptions.RequestException as e:
        return "ERROR", f"Lỗi kết nối: {str(e)[:80]}"


def main():
    print("=" * 70)
    print(" GEMINI API FULL MODELS DIAGNOSTIC TOOL ")
    print("=" * 70)

    keys_input = input(
        "Dán các API Keys (phân cách bằng dấu phẩy) hoặc Enter để nhập từng key:\n"
    ).strip()

    api_keys = []
    if "," in keys_input:
        api_keys = [k.strip() for k in keys_input.split(",") if k.strip()]
    else:
        if keys_input:
            api_keys.append(keys_input)
        while len(api_keys) < 4:
            k = input(f"Nhập API Key #{len(api_keys) + 1}: ").strip()
            if k:
                api_keys.append(k)

    print(f"\n[+] Đã nhận {len(api_keys)} Keys. Bắt đầu quét toàn bộ models...\n")

    logs = []

    for key_idx, key in enumerate(api_keys, 1):
        masked_key = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "INVALID_KEY"
        print(f"--> [Key #{key_idx}: {masked_key}] Đang lấy danh sách model...")

        models, err = get_all_generate_models(key)

        if models is None:
            print(f"    ❌ Lỗi: {err}")
            logs.append(
                {
                    "key_index": f"Key #{key_idx}",
                    "masked_key": masked_key,
                    "model": "ALL_MODELS",
                    "status": "KEY_ERROR",
                    "detail": err,
                }
            )
            continue

        print(
            f"    Found {len(models)} models hỗ trợ generateContent. Đang test thử từng model..."
        )

        for model_full_name in models:
            # Rút gọn tên hiển thị (bỏ tiền tố "models/")
            clean_model_name = model_full_name.replace("models/", "")

            status, detail = test_model(key, model_full_name)
            logs.append(
                {
                    "key_index": f"Key #{key_idx}",
                    "masked_key": masked_key,
                    "model": clean_model_name,
                    "status": status,
                    "detail": detail,
                }
            )
            print(f"    - {clean_model_name:<30} : {status}")
            time.sleep(0.3)

    # In Log để gửi lại
    print("\n" + "=" * 80)
    print("=== BÁO CÁO LOG KẾT QUẢ (COPY TOÀN BỘ ĐOẠN DƯỚI ĐÂY GỬI LẠI CHO TÔI) ===")
    print("=" * 80)

    output_log = "=== GEMINI FULL MODELS DIAGNOSTIC REPORT ===\n"
    for log in logs:
        output_log += f"[{log['key_index']}] [{log['masked_key']}] | Model: {log['model']:<30} | Status: {log['status']:<12} | Detail: {log['detail']}\n"
    output_log += "================================================="

    print(output_log)


if __name__ == "__main__":
    main()
