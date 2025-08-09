import hashlib
import json
from flask import Flask, request, jsonify, render_template
import time
import os
import sqlite3

# --- The MerkleTree class and verify_proof function remain unchanged ---
class MerkleTree:
    def __init__(self):
        self.leaves = []
        self.levels = []
    def _hash_data(self, data):
        encoded_data = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(encoded_data).hexdigest()
    def add_leaf(self, data):
        self.leaves.append(self._hash_data(data))
    def build(self):
        if not self.leaves: return None
        current_level = self.leaves
        self.levels = [current_level]
        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])
            next_level = []
            for i in range(0, len(current_level), 2):
                if current_level[i] < current_level[i+1]:
                    combined_data = current_level[i] + current_level[i+1]
                else:
                    combined_data = current_level[i+1] + current_level[i]
                new_hash = self._hash_data(combined_data)
                next_level.append(new_hash)
            self.levels.append(next_level)
            current_level = next_level
        return current_level[0]
    def get_proof(self, leaf_hash):
        proof = []
        try:
            idx = self.levels[0].index(leaf_hash)
        except ValueError:
            return None
        for level in self.levels[:-1]:
            if idx % 2 == 0:
                sibling_idx = idx + 1
            else:
                sibling_idx = idx - 1
            if sibling_idx < len(level):
                proof.append(level[sibling_idx])
            idx = idx // 2
        return proof

def verify_proof(leaf_hash, proof, root):
    calculated_hash = leaf_hash
    for sibling_hash in proof:
        if calculated_hash < sibling_hash:
            combined_data = calculated_hash + sibling_hash
        else:
            combined_data = sibling_hash + calculated_hash
        encoded_data = json.dumps(combined_data, sort_keys=True).encode('utf-8')
        calculated_hash = hashlib.sha256(encoded_data).hexdigest()
    return calculated_hash == root

# --- The AuditService class with the new get_all_sealed_roots method ---
class AuditService:
    DB_NAME = 'audit.db'

    def _get_db_connection(self):
        conn = sqlite3.connect(self.DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def add_log(self, log_data):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (log_data) VALUES (?)", (json.dumps(log_data),))
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return {"message": "Log received and stored.", "log_id": log_id}

    def seal_batch(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, log_data FROM logs WHERE batch_id IS NULL")
        unsealed_logs = cursor.fetchall()
        if not unsealed_logs:
            conn.close()
            return {"message": "No logs to seal."}
        tree = MerkleTree()
        log_dicts = [json.loads(log['log_data']) for log in unsealed_logs]
        for log_dict in log_dicts:
            tree.add_leaf(log_dict)
        merkle_root = tree.build()
        cursor.execute("INSERT INTO batches (merkle_root) VALUES (?)", (merkle_root,))
        batch_id = cursor.lastrowid
        for log in unsealed_logs:
            log_dict = json.loads(log['log_data'])
            leaf_hash = tree._hash_data(log_dict)
            proof = tree.get_proof(leaf_hash)
            cursor.execute(
                "UPDATE logs SET batch_id = ?, leaf_hash = ?, proof = ? WHERE id = ?",
                (batch_id, leaf_hash, json.dumps(proof), log['id'])
            )
        conn.commit()
        conn.close()
        return {
            "message": "Batch sealed successfully!",
            "batch_id": batch_id,
            "merkle_root": merkle_root,
            "logs_sealed_count": len(unsealed_logs)
        }
    
    def get_log_for_verification(self, log_id):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.log_data, l.proof, b.merkle_root
            FROM logs l
            JOIN batches b ON l.batch_id = b.id
            WHERE l.id = ?
        """, (log_id,))
        record = cursor.fetchone()
        conn.close()
        if not record:
            return None
        return {
            "log_data": json.loads(record['log_data']),
            "proof": json.loads(record['proof']),
            "root": record['merkle_root']
        }
    
    # --- NEW: Method to fetch all sealed roots from the database ---
    def get_all_sealed_roots(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, merkle_root, created_at FROM batches ORDER BY created_at DESC")
        batches = cursor.fetchall()
        conn.close()
        # Convert the list of Row objects into a dictionary
        return {batch['id']: {"merkle_root": batch['merkle_root'], "created_at": batch['created_at']} for batch in batches}


# --- Flask App Setup ---
API_SECRET_KEY = "my-super-secret-key-@@@@@@@@"
service = AuditService()
app = Flask(__name__)

# --- API Endpoints ---
@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/log', methods=['POST'])
def handle_log():
    request_key = request.headers.get('X-Api-Key')
    if not request_key or request_key != API_SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    result = service.add_log(request.get_json())
    return jsonify(result), 202

@app.route('/seal', methods=['POST'])
def handle_seal():
    request_key = request.headers.get('X-Api-Key')
    if not request_key or request_key != API_SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    result = service.seal_batch()
    return jsonify(result), 201

@app.route('/verify/log/<int:log_id>', methods=['GET'])
def handle_verify_by_id(log_id):
    verification_data = service.get_log_for_verification(log_id)
    if not verification_data:
        return jsonify({"error": "Log not found or not part of a sealed batch."}), 404
    leaf_hash = MerkleTree()._hash_data(verification_data['log_data'])
    is_valid = verify_proof(leaf_hash, verification_data['proof'], verification_data['root'])
    if is_valid:
        return jsonify({"verified": True, "message": "Log is authentic and part of the batch."})
    else:
        return jsonify({"verified": False, "message": "Verification failed."})

# --- MODIFIED: This endpoint now correctly queries the database ---
@app.route('/roots', methods=['GET'])
def get_roots():
    all_roots = service.get_all_sealed_roots()
    return jsonify(all_roots)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)