import random
import time

SIZE = 4800000
TOTAL_BITS = SIZE * 8

rng = random.Random()
A = bytearray(rng.randbytes(SIZE))
B = bytearray(A)

bit_positions = rng.sample(range(TOTAL_BITS), k=7)
for bit_pos in bit_positions:
    B[bit_pos // 8] ^= 1 << (bit_pos % 8)


def diff_only_16bit(a: bytearray, b: bytearray):
    """異なる 16bit (2byte) ブロックの (a_chunk, b_chunk) だけを返す"""
    if len(a) != len(b):
        raise ValueError("長さが異なります")

    diffs = []
    limit = len(a) - (len(a) % 2)
    for i in range(0, limit, 2):
        # 2バイト単位で比較し、違えばそのまま取り出す（順番・位置情報は持たない）
        chunk_a = bytes(a[i : i + 2])
        chunk_b = bytes(b[i : i + 2])
        if chunk_a != chunk_b:
            diffs.append((chunk_a, chunk_b))
    return diffs


ts = time.time()
diff_pairs = diff_only_16bit(A, B)
for ca, cb in diff_pairs:
    print(f"A: 0x{ca.hex()}  B: 0x{cb.hex()}")
print(f"-> Time spent (linear) : {time.time() - ts}")

print("================")

def diff_16bit_slice_no_mv(a: bytearray, b: bytearray):
    """毎回スライスした bytearray を渡す二分探索（memoryview 不使用）"""
    if len(a) != len(b):
        raise ValueError("長さが異なります")

    usable_len = len(a) - (len(a) % 2)
    a = a[:usable_len]
    b = b[:usable_len]

    if usable_len == 0 or a == b:
        return []

    if usable_len == 2:
        return [(bytes(a), bytes(b))]

    # 2バイト単位のブロック数で半分に割る（必ず偶数バイトになる）
    half_blocks = (usable_len // 2) // 2
    if half_blocks == 0:
        half_blocks = 1
    mid = half_blocks * 2

    return diff_16bit_slice_no_mv(a[:mid], b[:mid]) + diff_16bit_slice_no_mv(a[mid:], b[mid:])

ts = time.time()
for ca, cb in diff_16bit_slice_no_mv(A, B):
    print(f"A: 0x{ca.hex()}  B: 0x{cb.hex()}")
print(f"-> Time spent (binary without mv) : {time.time() - ts}")

print("================")

def diff_16bit_binary_search(a: bytearray, b: bytearray):
    """二分探索で異なる 16bit (2byte) ブロックの (a_2byte, b_2byte) を集める"""
    if len(a) != len(b):
        raise ValueError("長さが異なります")

    # 16ビット（2バイト）単位で揃えるため、末尾の余り1バイトは除外
    usable_len = len(a) - (len(a) % 2)
    if usable_len == 0:
        return []

    mv_a = memoryview(a)[:usable_len]
    mv_b = memoryview(b)[:usable_len]
    diffs = []

    def search(start: int, end: int):
        # 範囲内に差分がなければ即枝刈り（O(1) 相当のメモリビュー比較）
        if mv_a[start:end] == mv_b[start:end]:
            return

        # 16ビット（2バイト）単位まで絞り込めたら差分を追加
        if end - start == 2:
            diffs.append((bytes(mv_a[start:end]), bytes(mv_b[start:end])))
            return

        # 2バイト（16ビット）境界を崩さないように mid を偶数に合わせる
        mid = ((start + end) // 2) & ~1
        if mid == start:
            mid = start + 2
        elif mid == end:
            mid = end - 2

        search(start, mid)
        search(mid, end)

    search(0, usable_len)
    return diffs

ts = time.time()
for ca, cb in diff_16bit_binary_search(A, B):
    print(f"A: 0x{ca.hex()}  B: 0x{cb.hex()}")
print(f"-> Time spent (binary with mv) : {time.time() - ts}")
