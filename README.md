# FromBitToQubit
Hành trình từ máy tính cổ điển đến lượng tử

## Backend

```bash
pip install -r requirements.txt
python quantum_backend.py          # mở http://localhost:5000
python -m pytest test_quantum_analysis.py
```

Mở `http://localhost:5000` để dùng giao diện 3D trên trình duyệt (`web/index.html`, Three.js, không cần Unity): mỗi qubit là một Bloch sphere, dây vàng là rối lượng tử giữa hai qubit, đường nét đứt là tương quan không rối (ví dụ GHZ). Thanh thời gian bên dưới chạy mạch từng cổng (phím ← → và Space), qubit đang chịu tác động sẽ sáng lên.

`POST /simulate` với `{"qiskit_code": "..."}` trả về, ngoài statevector và xác suất:

- `qubits[i]`: `bloch_vector` [x, y, z], `purity`, `entropy`, `entangled` — tính từ ma trận mật độ rút gọn (`partial_trace`)
- `steps`: trạng thái sau từng cổng (bước 0 là |0…0⟩), mỗi bước có `gate` {`name`, `qubits`, `params`} và cùng các trường phân tích như trên. Bằng `null` nếu mạch có hơn 200 cổng.
- `pairs[k]`: `concurrence` (rối giữa 2 qubit) và `mutual_information` (tổng tương quan) cho từng cặp qubit

Toàn bộ phần vật lý nằm trong `quantum_analysis.py` và dùng `qiskit.quantum_info`.
