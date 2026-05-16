import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Graph Playground", layout="wide")

st.markdown("""
    <style>
    .main, .stApp { background-color: #FFFFFF !important; }
    .stButton>button {
        width: 100%; height: 3.5em; border-radius: 12px;
        font-weight: bold; background-color: #007bff !important; color: white !important;
    }
    div.stButton > button[key="clear_btn"] { background-color: #dc3545 !important; }
    input { height: 3em !important; font-size: 16px !important; }
    .result-box {
        background-color: #f8f9fa; padding: 15px; border-radius: 12px;
        border: 1px solid #dee2e6; margin: 10px 0;
    }
    .theory-box {
        background-color: #fff3cd; padding: 15px; border-radius: 12px;
        border: 1px solid #ffeeba; margin: 10px 0; color: #856404; line-height: 1.6;
    }
    iframe { border: 1px solid #ddd !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state: st.session_state.edges = [] 
if 'nodes' not in st.session_state: st.session_state.nodes = set()

path_nodes, best_edge_ids = [], []

st.title("📍 CHÀO MỪNG ĐẾN VỚI WEBSITE VỀ LÝ THUYẾT ĐỒ THỊ(version 1)")
st.markdown("---")
with st.container(border=True):
    st.write("Đây là phiên bản ra mắt đầu tiên nên không tránh khỏi những thiếu sót ngoài ý muốn. Chúng tôi rất mong nhận được ý kiến đóng góp của bạn qua biểu mẫu dưới đây để không ngừng hoàn thiện trải nghiệm.")
    st.link_button("Biểu mẫu góp ý", "https://forms.gle/tdZpNHsAxoqpgt5b8")
st.info("💡 Hướng dẫn sử dụng cơ bản: Nhập tên các điểm (A, B, C...) và trọng số (nếu có) để tạo ra các cạnh của đồ thị. Website sẽ tự động vẽ đồ thị và phân tích các tính chất toán học như đường đi có tổng trọng số nhỏ nhất; chu trình và đường đi Euler, Hamilton ở các mục bên dưới.")
    # --- 2. THÔNG BÁO & QUẢN LÝ ĐƯỜNG NỐI ---
with st.expander("➕ QUẢN LÝ ĐƯỜNG NỐI", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1])
    u = col1.text_input("Điểm đầu/Điểm cần xóa", key="u_input").upper().strip()
    v = col2.text_input("Điểm cuối", key="v_input").upper().strip()
    
    # Lựa chọn loại trọng số
    w_type = st.radio("Loại trọng số", ["Có giá trị", "Không có"], horizontal=True)
    if w_type == "Có giá trị":
        w = col3.number_input("Khoảng cách", min_value=0.1, value=5.0)
    else:
        w = 1.0 
        col3.markdown("<br><i>Mặc định = 1.0</i>", unsafe_allow_html=True)

    st.write("---") # Đường kẻ phân cách cho thoáng
    
    # ĐƯA NÚT BẤM RA NGOÀI KHỐI IF/ELSE TRÊN
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        if st.button("Thêm đường nối", use_container_width=True):
            if u and v and u != v:
                existing_edge = next((e for e in st.session_state.edges if (e['from'] == u and e['to'] == v) or (e['from'] == v and e['to'] == u)), None)
                if existing_edge:
                    existing_edge['weight'] = w
                    st.success(f"✅ Cập nhật {u}-{v}")
                else:
                    edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
                    st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id, 'is_weighted': (w_type == "Có giá trị")})
                    st.session_state.nodes.update([u, v])
                    st.success(f"✅ Đã thêm {u}-{v}")
                st.rerun()

    with btn_col2:
        if st.button("Xóa đường nối", use_container_width=True):
            if u and v:
                initial_count = len(st.session_state.edges)
                st.session_state.edges = [e for e in st.session_state.edges if not ((e['from'] == u and e['to'] == v) or (e['from'] == v and e['to'] == u))]
                if len(st.session_state.edges) < initial_count:
                    st.success(f"🗑️ Đã xóa nối {u}-{v}")
                    st.rerun()
                else:
                    st.error("❌ Không tìm thấy nối")

    with btn_col3:
        if st.button("Xóa điểm", use_container_width=True):
            # Ưu tiên xóa điểm ở ô "Từ điểm" (u) nếu có, không thì xóa v
            target_node = u if u else (v if v else None)
            
            if target_node and target_node in st.session_state.nodes:
                # 1. Xóa điểm khỏi tập hợp nodes
                st.session_state.nodes.remove(target_node)
                # 2. Xóa tất cả các đường nối liên quan đến điểm đó
                st.session_state.edges = [e for e in st.session_state.edges if e['from'] != target_node and e['to'] != target_node]
                
                st.success(f"🗑️ Đã xóa điểm {target_node} và các nối liên quan!")
                st.rerun()
            else:
                st.error("❌ Điểm không tồn tại")

G_simple = nx.Graph()
G_simple.add_nodes_from(st.session_state.nodes)
for e in st.session_state.edges:
    G_simple.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])

if st.session_state.nodes:
    # --- DIJKSTRA (PHIÊN BẢN MÔ PHỎNG CHI TIẾT TỪNG BƯỚC) ---
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT", expanded=False):
        c1, c2 = st.columns(2)
        start_node = c1.selectbox("Điểm đi", sorted(list(st.session_state.nodes)))
        end_node = c2.selectbox("Điểm đến", sorted(list(st.session_state.nodes)))
        
        if st.button("🚀 TÌM!!"):
            try:
                # 1. Tính toán kết quả cuối cùng trước
                path_nodes = nx.shortest_path(G_simple, source=start_node, target=end_node, weight='weight')
                total_dist = nx.shortest_path_length(G_simple, source=start_node, target=end_node, weight='weight')
                best_edge_ids = [G_simple[path_nodes[i]][path_nodes[i+1]]['id'] for i in range(len(path_nodes)-1)]
                
                # 2. Hiển thị kết quả lộ trình
                st.markdown(f'''
                <div class="result-box">
                    1. Đường đi ngắn nhất từ <b>{start_node}</b> đến <b>{end_node}</b> có lộ trình là: 
                    <span style="color:#007bff;"><b>{" ➔ ".join(path_nodes)}</b></span><br>
                    2. Tổng độ dài đường đi là: <span style="color:red;"><b>{total_dist}</b></span>
                </div>
                ''', unsafe_allow_html=True)
                
                # 3. Thuật toán mô phỏng từng bước để lấy dữ liệu thực tế
                steps_html = []
                unvisited = set(G_simple.nodes())
                distances = {node: float('inf') for node in G_simple.nodes()}
                distances[start_node] = 0
                step_idx = 1
                
                while unvisited:
                    # Chọn đỉnh có khoảng cách nhỏ nhất trong tập chưa thăm
                    curr = min(unvisited, key=lambda node: distances[node])
                    
                    if distances[curr] == float('inf'): break 
                    
                    # DÒNG QUAN TRỌNG: Ghi nhận nhãn vĩnh viễn tại bước này
                    log = f"<b>Bước {step_idx}:</b> Chọn đỉnh <b>{curr}</b>. Xác định <b>nhãn vĩnh viễn</b> cho {curr} là: <span style='color:green;'><b>{distances[curr]}</b></span>."
                    
                    updates = []
                    for neighbor in G_simple.neighbors(curr):
                        if neighbor in unvisited:
                            weight = G_simple[curr][neighbor].get('weight', 1.0)
                            new_dist = distances[curr] + weight
                            if new_dist < distances[neighbor]:
                                distances[neighbor] = new_dist
                                updates.append(f"cập nhật nhãn tạm thời {neighbor} = {new_dist}")
                    
                    if updates:
                        log += "<br>&nbsp;&nbsp;&nbsp;➔ <i>Duyệt các đỉnh kề: " + ", ".join(updates) + ".</i>"
                    else:
                        log += "<br>&nbsp;&nbsp;&nbsp;➔ <i>Không có nhãn tạm thời nào được cập nhật thêm.</i>"
                    
                    steps_html.append(log)
                    unvisited.remove(curr)
                    step_idx += 1
                    
                    if curr == end_node: break

                all_steps_text = "<br><br>".join(steps_html)
                st.markdown(f'''
                <div class="theory-box">
                    <b>3. CÁC BƯỚC THỰC HIỆN CỦA THUẬT TOÁN TRÊN ĐỒ THỊ NÀY:</b><br><br>
                    {all_steps_text}
                </div>
                ''', unsafe_allow_html=True)
                
            except nx.NetworkXNoPath:
                st.error(f"❌ Không tìm thấy đường đi từ {start_node} đến {end_node}!")
            except Exception as e:
                st.error(f"Lỗi: {e}")

    # --- CODE EULER ---
    with st.expander("📐 PHÂN TÍCH EULER", expanded=False):
        if st.button("🔍 KIỂM TRA EULER"):
            degrees = dict(G_simple.degree())
            odd_nodes = [n for n, d in degrees.items() if d % 2 != 0]
            is_connected = nx.is_connected(G_simple) if len(st.session_state.nodes) > 1 else True
            deg_desc = ", ".join([f"đỉnh <b>{n}</b> bậc <b>{d}</b>" for n, d in sorted(degrees.items())])
            
            if not is_connected:
                st.markdown(f'''
                <div class="theory-box">
                    ❌ <b>Đồ thị không có chu trình hay đường đi Euler.</b><br>
                    <b>Giải thích:</b> Đồ thị không liên thông nên không thỏa mãn điều kiện cần để tồn tại lộ trình Euler.
                </div>
                ''', unsafe_allow_html=True)
            elif len(odd_nodes) == 0:
                circuit = list(nx.eulerian_circuit(G_simple))
                path_nodes = [u for u, v in circuit] + [circuit[-1][1]]
                best_edge_ids = [G_simple[u][v]['id'] for u, v in circuit]
                st.markdown(f'''
                <div class="theory-box">
                    ✅ <b>Đồ thị có chu trình Euler.</b><br>
                    <b>Giải thích:</b> Ta thấy các đỉnh: {deg_desc} đều là số chẵn và đồ thị liên thông nên có chu trình Euler.<br>
                    <b>Chu trình:</b> <b>{" ➔ ".join(path_nodes)}</b>
                </div>
                ''', unsafe_allow_html=True)
            elif len(odd_nodes) == 2:
                u_s, v_e = odd_nodes[0], odd_nodes[1]
                path_gen = list(nx.eulerian_path(G_simple, source=u_s))
                path_nodes = [u for u, v in path_gen] + [path_gen[-1][1]]
                best_edge_ids = [G_simple[u][v]['id'] for u, v in path_gen]
                st.markdown(f'''
                <div class="theory-box">
                    ✅ <b>Đồ thị chỉ có đường đi Euler.</b><br>
                    <b>Giải thích:</b> Ta thấy các đỉnh: {deg_desc} và có đúng hai đỉnh <b>{u_s}</b> và <b>{v_e}</b> có bậc lẻ. Ngoài ra đồ thị liên thông nên có đường đi Euler từ {u_s} đến {v_e}.<br>
                    <b>Đường đi:</b> <b>{" ➔ ".join(path_nodes)}</b>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="theory-box">
                    ❌ <b>Đồ thị không có chu trình hay đường đi Euler.</b><br>
                    <b>Giải thích:</b> Ta thấy các đỉnh: {deg_desc}. Vì đồ thị có <b>{len(odd_nodes)} đỉnh bậc lẻ</b> (không phải 0 hoặc 2) nên không tồn tại chu trình hay đường đi Euler.
                </div>
                ''', unsafe_allow_html=True)

# --- CODE HAMILTON ---
    with st.expander("💎 PHÂN TÍCH HAMILTON", expanded=False):
        if st.button("🔍 KIỂM TRA HAMILTON"):
            n = len(st.session_state.nodes)
            if n < 3:
                st.warning("⚠️ Đồ thị cần ít nhất 3 đỉnh để xét các định lý Hamilton.")
            else:
                degrees = dict(G_simple.degree())
                nodes_sorted = sorted(list(st.session_state.nodes))
                
                # 1. Kiểm tra các định lý (Điều kiện đủ)
                # Hệ quả Ore (Định lý Dirac)
                min_deg_required = n / 2
                dirac_ok = all(d >= min_deg_required for d in degrees.values())
                
                # Định lý Ore
                ore_ok = True
                pairs_list = [] # Lưu danh sách các cặp (A, C)
                sums_list = []  # Lưu danh sách tổng bậc 3+3=6
                
                for i, u_n in enumerate(nodes_sorted):
                    for v_n in nodes_sorted[i+1:]:
                        if not G_simple.has_edge(u_n, v_n):
                            sum_deg = degrees[u_n] + degrees[v_n]
                            pairs_list.append(f"({u_n}, {v_n})")
                            sums_list.append(f"{degrees[u_n]}+{degrees[v_n]}={sum_deg}")
                            if sum_deg < n:
                                ore_ok = False
                # Nếu đồ thị đầy đủ (không có cặp nào không kề nhau) thì Ore vẫn thỏa mãn
                if not pairs_list and n >= 3:
                    ore_ok = True
                
                # Định lý đường đi Hamilton (d >= (n-1)/2)
                path_min_deg_required = (n - 1) / 2
                path_theorem_ok = all(d >= path_min_deg_required for d in degrees.values())
    
                # 2. Thuật toán vét cạn (Backtracking) tìm lộ trình thực tế
                def find_hamilton():
                    def backtrack(curr, path):
                        if len(path) == n:
                            return path
                        for neighbor in G_simple.neighbors(curr):
                            if neighbor not in path:
                                res = backtrack(neighbor, path + [neighbor])
                                if res: return res
                        return None
                    
                    # Ưu tiên tìm chu trình trước
                    for start in nodes_sorted:
                        p = backtrack(start, [start])
                        if p:
                            if G_simple.has_edge(p[-1], p[0]):
                                return p + [p[0]], "circuit"
                    
                    # Nếu không có chu trình, tìm đường đi
                    for start in nodes_sorted:
                        p = backtrack(start, [start])
                        if p:
                            return p, "path"
                    return None, None
    
                res_path, res_type = find_hamilton()
    
                # 3. Tổng hợp giải thích
                deg_details = ", ".join([f"đỉnh {node} (bậc {d})" for node, d in degrees.items()])
                
                if res_path:
                    path_nodes = res_path
                    best_edge_ids = [G_simple[path_nodes[i]][path_nodes[i+1]]['id'] for i in range(len(path_nodes)-1)]
                    
                    if res_type == "circuit":
                        status = "✅ Đồ thị có chu trình Hamilton."
                        if dirac_ok:
                            reason = (f"Thỏa mãn định lý Dirac: Đồ thị có <b>n = {n} đỉnh, các {deg_details} "
                                      f"đều có bậc không nhỏ hơn n/2 = {min_deg_required}.")
                        elif ore_ok:
                            pairs_str = ", ".join(pairs_list) if pairs_list else "Không có (đồ thị đầy đủ)"
                            sums_str = ", ".join(sums_list) if sums_list else "N/A"
                            
                            reason = (f"Thỏa mãn <b>định lý Ore</b>: Đồ thị có n = {n} đỉnh.<br>"
                                      f"Các cặp đỉnh không kề nhau lần lượt là: {pairs_str}.<br>"
                                      f"Tổng bậc của chúng lần lượt là: {sums_str} và đều không nhỏ hơn {n}.<br>"
                                      f"Vì vậy đồ thị thỏa mãn định lý Ore nên có chu trình Hamilton.")
                        else:
                            reason = (f"Đồ thị tồn tại chu trình Hamilton được tìm thấy bằng phương pháp vét cạn. "
                                      f"Lưu ý: Đồ thị này không thỏa mãn các điều kiện đủ (Dirac/Ore), "
                                      f"nhưng vì các định lý này chỉ mang tính một chiều nên một số đồ thị vẫn có thể có chu trình.")
                    else:
                        status = "✅ Đồ thị có đường đi Hamilton (không có chu trình Hamilton)."
                        if path_theorem_ok:
                            reason = (f"Thỏa mãn định lý về đường đi: Đồ thị có <b>n = {n} đỉnh, các {deg_details} "
                                      f"đều có bậc không nhỏ hơn (n-1)/2 = {path_min_deg_required}.")
                        else:
                            reason = (f"Đồ thị tồn tại đường đi Hamilton được tìm thấy bằng phương pháp vét cạn. "
                                      f"Lưu ý: Các điều kiện đủ về bậc đỉnh không được thỏa mãn, nhưng đường đi vẫn tồn tại.")
    
                    st.markdown(f'''
                    <div class="theory-box">
                        {status}<br>
                        <b>Phân tích bậc:</b> Số đỉnh <b>n = {n}</b>; {deg_details}.<br>
                        <b>Giải thích:</b> {reason}<br>
                        <b>Lộ trình:</b> {" ➔ ".join(path_nodes)}
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.warning("❌ Không tìm thấy chu trình hay đường đi Hamilton.")
                    st.info(f"Dựa trên kiểm tra vét cạn, không tồn tại lộ trình đi qua mỗi đỉnh đúng một lần. "
                            f"Bậc các đỉnh hiện tại: {deg_details}. Để chắc chắn có đường đi, "
                            f"mọi đỉnh cần có bậc tối thiểu là {path_min_deg_required}.")
# --- HIỂN THỊ ĐỒ THỊ ---
st.write("---")
c1, c2 = st.columns([3, 1]) # Chia tỷ lệ 3:1 để nút xóa nằm gọn bên phải
with c1:
    show_labels = st.checkbox("Hiển thị trọng số trên hình", value=True)
with c2:
    if st.button("🗑️ XÓA ĐỒ THỊ", key="clear_btn"):
        st.session_state.edges, st.session_state.nodes = [], set()
        components.html("<script>localStorage.clear(); window.parent.location.reload();</script>")
        st.rerun()

net = Network(height="550px", width="100%", bgcolor="#ffffff", font_color="black")
net.set_options('{"physics": {"enabled": false}, "interaction": {"navigationButtons": true}}')

for node in st.session_state.nodes:
    is_p = node in path_nodes
    net.add_node(node, label=node, color="#FF1E1E" if is_p else "#2196F3", size=30 if is_p else 25)

tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    tracker[pair] = tracker.get(pair, 0) + 1
    is_p = e['id'] in best_edge_ids
    
    # Xử lý hiển thị nhãn trọng số
    edge_label = ""
    if show_labels:
        edge_label = str(e['weight']) if e.get('is_weighted', True) else ""

    net.add_edge(e['from'], e['to'], label=edge_label, 
                 color="#FF1E1E" if is_p else "#D3D3D3", width=8 if is_p else 2, 
                 smooth={"type": "curvedCW", "roundness": 0.2 * (tracker[pair]-1) if tracker[pair]>1 else 0})

raw_html = net.generate_html()
custom_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var savedPos = JSON.parse(localStorage.getItem('nodePositions') || '{}');
        Object.keys(savedPos).forEach(function(id) { network.moveNode(id, savedPos[id].x, savedPos[id].y); });
        network.on("dragEnd", function(params) {
            if (params.nodes.length > 0) {
                var id = params.nodes[0];
                var pos = network.getPositions([id])[id];
                var curPos = JSON.parse(localStorage.getItem('nodePositions') || '{}');
                curPos[id] = pos;
                localStorage.setItem('nodePositions', JSON.stringify(curPos));
            }
        });
    }, 500); 
});
</script>
"""
components.html(raw_html.replace("</body>", custom_js + "</body>"), height=600)
