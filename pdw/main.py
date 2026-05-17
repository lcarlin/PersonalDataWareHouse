import sys

from pdw.core.orchestrator import run_pipeline


def main(param_file):
    run_pipeline(param_file)


if __name__ == '__main__':
    input_param_file = ""

    if len(sys.argv) == 2:
        input_param_file = sys.argv[1]

    main(input_param_file)

# EOP
