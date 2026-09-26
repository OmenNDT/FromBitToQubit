# FromBitToQubit
Hành trình từ máy tính cổ điển đến lượng tử

## Backend

```bash
pip install -r requirements.txt
python quantum_backend.py          # mở http://localhost:5000
python -m pytest test_quantum_analysis.py
```

Tab **Bài học** gồm 8 chương đi từ bit cổ điển đến dịch chuyển lượng tử: chồng chất và giao thoa, pha, rối lượng tử, đo lường và sụp đổ, GHZ, thuật toán Deutsch. Mỗi bước trong mạch có lời giải thích riêng. Nội dung nằm trong `web/lessons.json`, và mỗi phần tử `notes` ứng với một bước (bước 0 là trạng thái ban đầu). Tab **Tự do** để thử mạch của riêng bạn.

Mở `http://localhost:5000` để dùng giao diện 3D trên trình duyệt (`web/index.html`, Three.js, không cần Unity): mỗi qubit là một Bloch sphere, dây vàng là rối lượng tử giữa hai qubit, đường nét đứt là tương quan không rối (ví dụ GHZ). Thanh thời gian bên dưới chạy mạch từng cổng (phím ← → và Space), qubit đang chịu tác động sẽ sáng lên.

`POST /simulate` với `{"qiskit_code": "..."}` trả về, ngoài statevector và xác suất:

- `qubits[i]`: `bloch_vector` [x, y, z], `purity`, `entropy`, `entangled` — tính từ ma trận mật độ rút gọn (`partial_trace`)
- `steps`: trạng thái sau từng cổng (bước 0 là |0…0⟩), mỗi bước có `gate` {`name`, `qubits`, `params`} và cùng các trường phân tích như trên. Bằng `null` nếu mạch có hơn 200 cổng.
- Mạch có `measure`: mỗi bước đo lấy mẫu một kết quả và làm trạng thái sụp đổ (`gate.outcome`, `clbits`); `counts` là thống kê `shots` lần chạy bằng Qiskit Aer. Truyền `seed` để lặp lại đúng kết quả.
- `pairs[k]`: `concurrence` (rối giữa 2 qubit) và `mutual_information` (tổng tương quan) cho từng cặp qubit

Toàn bộ phần vật lý nằm trong `quantum_analysis.py` và dùng `qiskit.quantum_info`.
