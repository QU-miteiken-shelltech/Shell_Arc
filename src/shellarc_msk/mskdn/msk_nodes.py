class MSKDN_Port:
    def __init__(self, node, name, is_output, node_expression=None):
        self.node = node
        self.name = name
        self.is_output = is_output
        self.node_expression = node_expression
        self.wires = []

    @property
    def is_input(self):
        return not self.is_output

    def can_connect(self, other):
        """別のノードの、反対向きのポートとだけ繋げる。"""
        return other.node is not self.node and self.is_output != other.is_output


class MSKDN_Wire:
    def __init__(self, start_port, end_port=None, wire_expression=None):
        """start_port=出力ポート、end_port=入力ポート。
        end_port が None なら未接続 (UI のドラッグ中の仮配線用で、ポートには登録しない)。"""
        self.start_port = start_port
        self.end_port = None
        self.wire_expression = wire_expression
        if end_port is not None:
            self.connect(end_port)

    def connect(self, end_port):
        if not (self.start_port.is_output and self.start_port.can_connect(end_port)):
            raise ValueError("出力ポートから、別ノードの入力ポートへのみ接続できます")
        self.end_port = end_port
        self.start_port.wires.append(self)
        end_port.wires.append(self)

    def refresh(self):
        """端点が動いたときに呼ばれる。UI 側で再描画する。"""


class MSKDN_Node:
    def __init__(self, title="Node"):
        self.title = title
        self.inputs = []
        self.outputs = []

    def create_port(self, name, is_output):
        """UI 側でオーバーライドして UI ポートを返す。"""
        return MSKDN_Port(self, name, is_output)

    def on_ports_changed(self):
        """ポートが増えた後に呼ばれる。UI 側でレイアウトする。"""

    def add_input(self, name):
        port = self.create_port(name, False)
        self.inputs.append(port)
        self.on_ports_changed()
        return port

    def add_output(self, name):
        port = self.create_port(name, True)
        self.outputs.append(port)
        self.on_ports_changed()
        return port

    def refresh_wires(self):
        for port in self.inputs + self.outputs:
            for wire in port.wires:
                wire.refresh()