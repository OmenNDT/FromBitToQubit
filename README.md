# FromBitToQubit
Hành trình từ máy tính cổ điển đến lượng tử

## Backend

```bash
pip install -r requirements.txt
python quantum_backend.py          # http://localhost:5000
python -m pytest test_quantum_analysis.py
```

`POST /simulate` với `{"qiskit_code": "..."}` trả về, ngoài statevector và xác suất:

- `qubits[i]`: `bloch_vector` [x, y, z], `purity`, `entropy`, `entangled` — tính từ ma trận mật độ rút gọn (`partial_trace`)
- `pairs[k]`: `concurrence` (rối giữa 2 qubit) và `mutual_information` (tổng tương quan) cho từng cặp qubit

Toàn bộ phần vật lý nằm trong `quantum_analysis.py` và dùng `qiskit.quantum_info`.
