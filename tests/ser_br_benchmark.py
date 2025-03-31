import io
import os
import time
import cProfile
import pstats

from clvm.SExp import SExp
from clvm.serialize import sexp_from_stream, Backrefs


def benchmark_block_2500014() -> None:
    """
    Benchmark serialization of a large block with different backref strategies.
    """
    print("\nLoading block tests/block-2500014...")
    b1 = open("tests/block-2500014", "rb").read()
    s1: SExp = sexp_from_stream(io.BytesIO(b1), SExp.to)
    print(f"Original size: {len(b1)} bytes")

    profile_enabled = os.environ.get("PROFILE") == "1"
    profile_dir = "prof"
    if profile_enabled and not os.path.exists(profile_dir):
        os.makedirs(profile_dir)

    def run_and_profile(name: str, func, *args, **kwargs):
        print(f"\nBenchmarking serialization with backrefs ({name})...")
        prof_file = os.path.join(profile_dir, f"ser_br_{name}.prof")
        pr = cProfile.Profile() if profile_enabled else None

        now = time.time()
        if pr:
            pr.enable()

        result = func(*args, **kwargs)

        if pr:
            pr.disable()
            pr.dump_stats(prof_file)

        delta = time.time() - now
        print(f"  Serialized in {delta:.3f} seconds")
        print(f"  Size: {len(result)} bytes")

        if pr:
            print(f"  Profiling data saved to {prof_file}")
            with open(prof_file + ".txt", "w") as f:
                ps = pstats.Stats(pr, stream=f).sort_stats("cumulative")
                ps.print_stats()
            print(f"  Profiling stats summary saved to {prof_file}.txt")
            # Print top 15 cumulative time functions to console
            print("  Top 15 functions by cumulative time:")
            ps = pstats.Stats(pr).sort_stats("cumulative")
            ps.print_stats(15)

        return result

    b_disallow = run_and_profile("DISALLOW", s1.as_bin, allow_backrefs=Backrefs.DISALLOW)
    b_allow = run_and_profile("ALLOW", s1.as_bin, allow_backrefs=Backrefs.ALLOW)
    b_fast = run_and_profile("FAST", s1.as_bin, allow_backrefs=Backrefs.FAST)


    # Optional: Verify deserialization still works (can be slow)
    print("\nVerifying deserialization...")
    s_disallow = sexp_from_stream(io.BytesIO(b_disallow), SExp.to, allow_backrefs=False)
    assert s1 == s_disallow
    s_allow = sexp_from_stream(io.BytesIO(b_allow), SExp.to, allow_backrefs=True)
    assert s1 == s_allow
    s_fast = sexp_from_stream(io.BytesIO(b_fast), SExp.to, allow_backrefs=True)
    assert s1 == s_fast
    print("  Deserialization verified.")


if __name__ == "__main__":
    benchmark_block_2500014()
