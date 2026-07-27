# ----------------------------------------------------------
# 违规样本: 含有字面动作序列, 解析器必须拒绝
# ----------------------------------------------------------

order center_first [proof: none]

solution: jump(0,right), jump(3,left), jump(0,right)

prefer edge_jumps_last [ev: 3/5]
