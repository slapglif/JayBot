#!/usr/bin/env python
"""Silent daily wrapper for the prospective option-chain collector."""
import sys
import collect_prospective_option_chain as collector
sys.argv=[sys.argv[0],'--quiet']
raise SystemExit(collector.main())
