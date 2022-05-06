import argparse
import os.path
from logging import error

from scenario_conversion.osc_to_cr_converter import OscToCrConverter


def command_line_interface() -> None:
    """
    Parse and check command line arguments using the argparse module and then run the Os2CrConverter
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["import", "merge"], help="Specify the ")
    parser.add_argument("source_file", metavar="SOURCE_FILE_PATH")
    parser.add_argument("target_file", metavar="TARGET_FILE_PATH")
    parser.add_argument("--cr-files", dest="cr_files", nargs="+", required=False, help="Common Road Files")
    parser.add_argument("--non-interactive", dest="interactive", action="store_false")
    args = parser.parse_args()

    if args.mode == "merge" and len(args.cr_files) == 0:
        parser.error("With merge mode you need to specify Common Road Files with --cr-files to merge with")

    if not os.path.exists(args.source_file):
        error("Source filepath {} does not exist".format(args.source_file))
    if not os.path.exists(args.target_file):
        error("Target filepath {} does not exist".format(args.target_file))

    converter = OscToCrConverter(args.source_file)

    converter.run()

    if args.mode == "merge":
        converter.merge(args.cr_files)

    if args.interactive:
        converter.print_statistics()
        user_input = input("Want to continue saving to {} (y/yes)".format(args.target_file))
        if user_input.lower() not in ["y", "yes"]:
            exit(0)

    converter.save_to_file(args.target_file)


if __name__ == '__main__':
    command_line_interface()
