# Copyright (c) 2020 Espressif Systems (Shanghai) Co., Ltd.
#
# SPDX-License-Identifier: Apache-2.0

'''update.py

Espressif west extension to retrieve esp-idf submodules.'''

import configparser
import os
import platform
import subprocess
from pathlib import Path

from textwrap import dedent
from west.commands import WestCommand
from west import log

ESP_IDF_REMOTE = "https://github.com/zephyrproject-rtos/hal_espressif"
ZEPHYR_SUBMODULES = ".gitmodules"


def cmd_check(cmd, cwd=None, stderr=subprocess.STDOUT):
    return subprocess.check_output(cmd, cwd=cwd, stderr=stderr)


def cmd_exec(cmd, cwd=None, shell=False):
    return subprocess.check_call(cmd, cwd=cwd, shell=shell)


class UpdateTool(WestCommand):

    def __init__(self):
        super().__init__(
            'espressif',
            # Keep this in sync with the string in west-commands.yml.
            'download toolchain or update ESP-IDF submodules',
            dedent('''
            This interface allows downloading Espressif toolchain
            or fetch ESP-IDF submodules required for
            Espressif SoC devices framework.'''),
            accepts_unknown_args=False)

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name,
                                         help=self.help,
                                         description=self.description)

        parser.add_argument('command', choices=['install', 'update'],
                            help='install espressif toolchain or fetch submodules')

        return parser

    def do_run(self, args, unknown_args):

        module_path = (
            Path(os.getenv("ZEPHYR_BASE")).absolute()
            / r".."
            / "modules"
            / "hal"
            / "espressif"
        )

        if not module_path.exists():
            log.die('cannot find espressif project in $ZEPHYR_BASE path')

        if args.command == "update":
            self.update(module_path)
        elif args.command == "install":
            self.install(module_path)

    def update(self, module_path):
        log.banner('updating ESP-IDF submodules..')

        os.chdir(module_path)
        cfg = configparser.ConfigParser()
        cfg.read(ZEPHYR_SUBMODULES)

        for k in cfg.sections():
            if not cfg.has_option(k, 'path') or not cfg.has_option(k, 'url'):
                continue

            path = cfg[k]['path']
            url = cfg[k]['url']
            
            branch = "master"
            if cfg.has_option(k, 'branch'):
                branch = cfg[k]['branch']

            if os.path.isdir(path):
                print('Updating', path)
                cmd_check(("git", "-C", path, "reset", "--hard"), cwd=module_path)
                cmd_check(("git", "-C", path, "pull", "origin", branch), cwd=module_path)
                cmd_check(("git", "-C", path, "checkout", branch), cwd=module_path)
            else:
                print('Cloning into', path)
                cmd_check(("git", "clone", url, path), cwd=module_path)
                cmd_check(("git", "-C", path, "checkout", branch), cwd=module_path)

        log.banner('updating ESP-IDF submodules completed')

    def install(self, module_path):

        log.banner('downloading ESP-IDF tools..')

        if platform.system() == 'Windows':
            cmd_exec(("python.exe", "tools/idf_tools.py", "--tools-json=tools/zephyr_tools.json", "install"),
                     cwd=module_path)
        else:
            cmd_exec(("./tools/idf_tools.py", "--tools-json=tools/zephyr_tools.json", "install"),
                     cwd=module_path)

        log.banner('downloading ESP-IDF tools completed')
