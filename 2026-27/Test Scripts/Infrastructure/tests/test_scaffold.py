from pathlib import Path
import shutil
import tomllib

import pytest

from new_board import create_board

ROOT = Path(__file__).resolve().parents[2]


def project(tmp_path):
    template = tmp_path/'Infrastructure/board_template'
    shutil.copytree(ROOT/'Infrastructure/board_template', template)
    return template


@pytest.mark.parametrize('name', ['BSPD_Test', 'New Board Test'])
def test_new_board_has_usable_clean_template(tmp_path, name):
    project(tmp_path)
    board = create_board(name, tmp_path)
    assert board == tmp_path/'Suites'/name
    assert (board/'test_identity.py').is_file()
    assert (board/'__init__.py').is_file()
    config = tomllib.loads((board/'bench.toml').read_text())
    assert config['instruments']['dmm']['address'] == ''
    assert config['limits']['glv_max_v'] == 14.4
    assert (board/'README.md').read_text().startswith(f'# {name}\n')


@pytest.mark.parametrize('name', ['../escape', 'Board/Other', 'CON', 'pytest', 'Board.', 'Board '])
def test_invalid_names_do_not_create_directories(tmp_path, name):
    project(tmp_path)
    with pytest.raises(ValueError): create_board(name, tmp_path)
    assert not (tmp_path/'Suites').exists()


def test_existing_board_and_case_variant_are_preserved(tmp_path):
    project(tmp_path)
    board = create_board('BSPD_Test', tmp_path)
    sentinel = board/'keep.txt'
    sentinel.write_text('existing work')
    for name in ('BSPD_Test', 'bspd_test'):
        with pytest.raises(FileExistsError): create_board(name, tmp_path)
    assert sentinel.read_text() == 'existing work'


def test_local_config_and_caches_are_not_copied(tmp_path):
    template = project(tmp_path)
    (template/'bench.toml').write_text('personal settings')
    (template/'__pycache__').mkdir()
    (template/'__pycache__/old.pyc').write_bytes(b'cache')
    board = create_board('New_Board', tmp_path)
    assert not (board/'__pycache__').exists()
    assert (board/'bench.toml').read_bytes() == (board/'bench.example.toml').read_bytes()
