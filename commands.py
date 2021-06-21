import sys
import argparse
from ast import literal_eval
from os import system, getcwd

from colors import bcolors
from Parser import pipeline
from configs.Configure import Configure


COMPANIES = ["hh.ru", "rabota.ru", "superjob.ru", "career.habr.com", "trud.com",
             "zarplata.ru", "worki.ru", "vakant.ru", "gorodrabot.ru"]

conf = Configure()
conf.update_config_data()

def menu() -> None:
    system("clear")
    print(f"""{bcolors.HEADERS}HGood time of day. This script is intended for parsing companies:{bcolors.ENDC}{bcolors.OKBLUE}{", ".join(COMPANIES)}{bcolors.ENDC}. 
{bcolors.HEADERS}and an argument in the form of your vacancy / skill{bcolors.ENDC}. 
The list of commands and parser settings can be seen by the magic command{bcolors.B}--help{bcolors.ENDC}""")

def subparser_arg(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(title='Parsers settings',
                                       description='Commands that are remembered for changes and that allow you to manage the parsing process')
    parser_setting = subparsers.add_parser("parser_settings",
                                           help="Setting for parser")
    parser_setting.add_argument("-cp", "--pagecount", type=int,
                                nargs=1, metavar="PAGES",
                                help="--parser_setting -cp [integer]. How many iterations will be done when parsing the page. Default=5")
    parser_setting.add_argument("-dp", "--drop_duplicate", type=str,
                                nargs=1, metavar="DROP_DUPL", choices=["True", "False"],
                                help="--parser_setting -dp [True/False]. Skips duplicate values when writing to a csv file. Default=True")
    parser_setting.add_argument("-gr", "--get_report", type=str,
                                nargs=1, metavar="GET_REPORT", choices=["True", "False"],
                                help="--parser_setting -gr [True/False]. Give a report on errors, the number of recorded and skipped data, the path to the file. Default=True")
    parser_setting.add_argument("-wf", "--write_to_file", type=str,
                                nargs=1, metavar="WRITE_FILE", choices=["True", "False"],
                                help="--parser_setting -wf [True/False]. Write data to a file that is in the specified path? If set to False, the values will be displayed directly in the console, Default=True")
    parser_setting.add_argument("-exp", "--exp_parsers", type=str,
                                nargs=1, metavar="EXP_PARSERS", choices=["True", "False"],
                                help="--parser_setting -exp [True/False]. Should I use experimental parsers that are still under development? PLEASE NOTE, the usual loading time of these parsers is 5 minutes, and there is a chance that they may not work on your device. Default=False")
    parser_setting.add_argument("-show", "--show_setting", type=str,
                                nargs="?", metavar="SHOW",
                                help="--parser_setting -show. Shows a list of current settings")

def parser_arg() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vacancies_parser",
        description="""
        This script is designed for parsing and recording vacancies from the list of companies. 
For parsing, you need to enter the url of the site that is in the list 
(NOTE, if the site has a job section as a side part, then you need to explicitly specify the url with the job section)
and the skill that will be searched for.
""",
        epilog="Parser_jobs 1.0.0 - Valentine Chernikh (2021). a simple script in a few hours..."
    )
    parser.add_argument('-p', '--pars', type=str,
                        nargs=1,metavar="PARSER",
                        help="--pars [skill]. Parses jobs by the specified skill")
    parser.add_argument('-s', '--search', type=str,
                        nargs=2,metavar="SEARCH",
                        help="--search [url] [skill]. Parses jobs by the specified url and skill")
    parser.add_argument('-l', '--list',
                        nargs="?",metavar="COMPANY_LIST",
                        help="--list. Displays a list of companies for which parsing is possible")
    parser.add_argument('-sp', '--setpathfile', type=str,
                        nargs=1,metavar="SET_PATHFILE",
                        help=f"--setpathfile [file path]. Assigns the file path. Default path is {getcwd()}")

    subparser_arg(parser)

    return parser

def commands():

    parser = parser_arg()
    args = parser.parse_args(sys.argv[1:])

    if len(sys.argv) >= 2:
        #  ---  main  parser ---
        if args.search:
            url = args.search[0]
            skill = args.search[1]
            # TODO: create get_site with argumetns form config
            print('Sorry, this is command under development')
            pass
        elif args.pars:
            kwargs = {"skill": str(args.pars[0]),
                      "file": str(conf.get_config_value("file", ["path", "name"])),
                      "write_to_file": literal_eval(conf.get_config_value("options", "write_to_file")),
                      "drop_duplicate": literal_eval(conf.get_config_value("options", "drop_duplicate")),
                      "pages": int(conf.get_config_value("options", "pages")),
                      "get_report": literal_eval(conf.get_config_value("options", "get_report")),
                      "experimental_parsers": literal_eval(conf.get_config_value("options", "experimental_parsers")),
                      }
            return pipeline(kwargs)
        elif sys.argv[1] == '--list' or sys.argv[1] == '-l':
            # pass
            print(f"{bcolors.OKBLUE}{', '.join(COMPANIES)}{bcolors.ENDC}")
        elif args.setpathfile:
            filepath = args.setpathfile[0]
            file = filepath + conf.get_config_value('file', 'name')+conf.get_config_value('file','format')
            with open(file, mode='a'):
                pass
            conf.set_config_value('file', 'path', file)
            print(f"{bcolors.OK}SUCCESS: file path to change to {file}{bcolors.ENDC}")

        # --- sub parser ---
        if sys.argv[-1].strip() == "parser_settings":
            # if user input is "date_settings" without arguments
            print(f"print [{sys.argv[1]}] [--help] for more informaion")
        elif args.pagecount:
            pages = args.pagecount[0]
            conf.set_config_value("options", "pages", str(pages))
            print(f"{bcolors.OK}SUCCESS: count of page change to {pages}{bcolors.ENDC}")
        elif args.drop_duplicate:
            answer = args.drop_duplicate[0]
            conf.set_config_value("options", "drop_duplicate", answer)
            print(f"{bcolors.OK}SUCCESS: value drop duplicate  change to {answer}{bcolors.ENDC}")
        elif args.get_report:
            answer = args.get_report[0]
            conf.set_config_value("options", "get_report", answer)
            print(f"{bcolors.OK}SUCCESS: value get report change to {answer}{bcolors.ENDC}")
        elif args.write_to_file:
            answer = args.write_to_file[0]
            conf.set_config_value("options", "write_to_file", answer)
            print(f"{bcolors.OK}SUCCESS: value write to file change to {answer}{bcolors.ENDC}")
        elif args.exp_parsers:
            answer = args.exp_parsers[0]
            conf.set_config_value("options", "experimental_parsers", answer)
            print(f"{bcolors.OK}SUCCESS: value experimental parsers change to {answer}{bcolors.ENDC}")
        elif sys.argv[2] == '--show' or sys.argv[2] == '-show':
            with open("configs/config.conf") as config:
                    for line in config.readlines():
                        row = line.split("=")
                        if len(row) > 1:  # ignored [section]
                            parameter = row[0]
                            value = row[1]
                            if parameter.strip() == "default":
                                continue
                            print(f"{bcolors.ORANGE}{parameter}{bcolors.ENDC} = {bcolors.PURPE}{value}{bcolors.ENDC}")
        else:
            print(f"{bcolors.WARNING}Unknown command {sys.argv[1:]}. Print{bcolors.ENDC} {bcolors.B}--help {bcolors.ENDC}"
                  f"{bcolors.WARNING}for more information{bcolors.ENDC}")
    else:
        menu()
