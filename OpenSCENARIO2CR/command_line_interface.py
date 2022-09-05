import argparse
import os.path
from logging import error

from Osc2CrConverter import Osc2CrConverter


def command_line_interface() -> None:
    """
    Parse and check command line arguments using the argparse module and then run the Os2CrConverter
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["import", "merge"], help="Specify the ")
    parser.add_argument("openscenario_file", metavar="SOURCE_FILE_PATH")
    parser.add_argument("target_file", metavar="TARGET_FILE_PATH")
    parser.add_argument("-d", "--opendrive", dest="opendrive_file", help="Optional Opendrive Map file")
    parser.add_argument("--cr-files", dest="cr_files", nargs="+", required=False, help="Common Road Files")
    parser.add_argument("--non-interactive", dest="interactive", action="store_false")
    args = parser.parse_args()

    if args.mode == "merge" and len(args.cr_files) == 0:
        parser.error("With merge mode you need to specify Common Road Files with --cr-files to merge with")

    if not os.path.exists(args.openscenario_file):
        error("Source filepath {} does not exist".format(args.openscenario_file))
        exit(0)
    if args.opendrive_file is not None and not os.path.exists(args.opendrive_file):
        error("Opendrive filepath {} does not exist".format(args.openscenario_file))
        exit(0)
    if os.path.exists(args.target_file):
        error("Target filepath {} does exist".format(args.target_file))

    converter = Osc2CrConverter(args.openscenario_file, args.opendrive_file)

    converter.run_conversion()

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
