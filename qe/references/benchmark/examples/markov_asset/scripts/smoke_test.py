"""
Smoke test: does each version's four priced assets actually run, exactly as the
lecture calls them? Prints PASS/ERROR per function.
"""
import traceback
import jax
import jax.numpy as jnp
import numpy as np

import model_old as old
import model_new as new


def try_old():
    print("=== OLD (numpy) ===")
    ap = old.AssetPriceModel(β=0.9)
    for name, fn in [
        ("tree_price", lambda: old.tree_price(old.AssetPriceModel())),
        ("consol_price", lambda: old.consol_price(ap, 1.0)),
        ("call_option", lambda: old.call_option(ap, 1.0, 40.0)),
        ("finite_horizon_call_option",
         lambda: old.finite_horizon_call_option(ap, 1.0, 40.0, 5)),
    ]:
        try:
            fn(); print(f"  PASS  {name}")
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")


def try_new():
    print("=== NEW (jax), called exactly as the lecture does ===")
    ap = new.create_ap_model(β=0.9)
    # tree_price
    try:
        err, v = new.tree_price_jit(new.create_ap_model()); err.throw()
        print("  PASS  tree_price_jit")
    except Exception as e:
        print(f"  ERROR tree_price_jit: {type(e).__name__}: {e}")
    # consol_price
    try:
        err, p = new.consol_price_jit(ap, 1.0); err.throw()
        print("  PASS  consol_price_jit")
    except Exception as e:
        print(f"  ERROR consol_price_jit: {type(e).__name__}: {e}")
    # call_option
    try:
        err, w = new.call_option_jit(ap, 1.0, 40.0); err.throw()
        print("  PASS  call_option_jit")
    except Exception as e:
        print(f"  ERROR call_option_jit: {type(e).__name__}: {e}")
    # finite_call_option
    try:
        err, w = new.finite_call_option_jit(ap, 1.0, 40.0, 5); err.throw()
        print("  PASS  finite_call_option_jit")
    except Exception as e:
        print(f"  ERROR finite_call_option_jit: {type(e).__name__}: {e}")


if __name__ == "__main__":
    try_old()
    try_new()
