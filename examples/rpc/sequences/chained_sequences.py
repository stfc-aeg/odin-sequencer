from odin_sequencer.rpc.client import OdinSequencerClient, OdinSequencerClientError


provides = [
    "test_seq",
    "test_client"
]

_client = None
def client():
    global _client
    if _client is None:
        _client = OdinSequencerClient(
            "127.0.0.1", ctrl_port=5555, log_port=6666, emit_exceptions=False, print_func=print
        )
    return _client

def test_seq():
    print("test sequence")

    # Create a client connected to a sequencer running at the specified address.
    seq = client()

    # Get a sequencer context object to interact with directly
    test_device = seq.get_context("test_device")

    result = test_device.execute("read_reg")
    print(f">>> Register value is {result}")

    result = seq.add(a=5, b=10)
    print(f">>> Result of add sequence is {result}")

def test_client():
    seq = client()

    result = seq.add(a=3, b=4)
    print(f">>> Result of repeated add sequence is {result}")
