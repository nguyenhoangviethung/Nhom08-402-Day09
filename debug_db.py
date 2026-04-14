import os
import chromadb

# CHỈ dùng chromadb, không dùng sentence_transformers để máy không bị treo
print("--- Đang kiểm tra dữ liệu thô trong ChromaDB ---")

# Lấy đường dẫn chuẩn
db_path = os.path.join(os.getcwd(), "chroma_db")

if not os.path.exists(db_path):
    print(f"❌ Thư mục '{db_path}' không tồn tại!")
else:
    try:
        # Kết nối client
        client = chromadb.PersistentClient(path=db_path)
        
        # Liệt kê collection
        collections = client.list_collections()
        print(f"✅ Đã kết nối. Tìm thấy {len(collections)} collections.")
        
        for col_info in collections:
            # Lấy collection mà không cần truyền embedding_function (để đọc số lượng thôi)
            col = client.get_collection(name=col_info.name)
            print(f"   👉 Collection '{col_info.name}' đang có: {col.count()} chunks")
            
    except Exception as e:
        print(f"❌ Lỗi đọc dữ liệu: {e}")

print("--- Kiểm tra xong ---")