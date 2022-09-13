# Copyright (c) 2019 Doctor Web, Ltd.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE

import os
import traceback

import mock
import pytest
from click.testing import CliRunner

from vxcube_api.__main__ import cli, main
from vxcube_api.cli_helpers import ClientConfig
from vxcube_api.errors import VxCubeApiException
from vxcube_api.objects import Sample
from vxcube_api.utils import UTF8_CONSOLE


def normal_execution(result):
    if result.exit_code == 0:
        return True
    else:
        print("Abnormal execution")
        print("Exit Code: {}".format(result.exit_code))
        print("Output: {}".format(result.output))
        if result.exc_info:
            traceback.print_exception(*result.exc_info)
        assert result.exit_code == 0


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert normal_execution(result)


@pytest.mark.parametrize(
    "exc, exit_code", [
        (VxCubeApiException, -1),
        (KeyboardInterrupt, -2),
        (Exception, -3)
    ]
)
def test_cli_raise_exceptions(exc, exit_code):
    with mock.patch("vxcube_api.__main__.cli", side_effect=exc("error")):
        with pytest.raises(SystemExit) as ex:
            main()
        assert ex.value.code == exit_code


def test_download_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["download", "--help"])

    assert normal_execution(result)
    assert "archive" in result.output
    assert "sample" in result.output


def test_login():
    api = mock.Mock()
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.__main__.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "login",
            "--login", "login",
            "--password", "password"
        ]
        result = runner.invoke(cli, params)

    assert normal_execution(result)
    assert "Mock" in result.output
    vxcube_api_cls.assert_called_with(base_url="http://test.url", version=42)
    api.login.assert_called_with(login="login", password="password", new_key=False)


def test_login_with_new_key():
    api = mock.Mock()
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.__main__.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "login",
            "--login", "login",
            "--password", "password",
            "--new-key"
        ]
        result = runner.invoke(cli, params)

    assert normal_execution(result)
    assert "Mock" in result.output
    vxcube_api_cls.assert_called_with(base_url="http://test.url", version=42)
    api.login.assert_called_with(login="login", password="password", new_key=True)


def test_upload_sample():
    sample = mock.Mock()
    api = mock.Mock(**{"upload_samples.return_value": [sample]})
    vxcube_api_cls = mock.Mock(return_value=api)
    runner = CliRunner()
    params = [
        "--base-url", "http://test.url",
        "--version", "42",
        "--api-key", "test-api-key",
        "upload",
        "test_sample_path"
    ]
    with runner.isolated_filesystem():
        with open("test_sample_path", "w") as f:
            f.write("test sample content")
        with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
            result = runner.invoke(cli, params)

    assert normal_execution(result)
    assert "Mock" in result.output
    assert "format not recognized" not in result.output
    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.upload_sample.assert_not_called()
    api.upload_samples.assert_called_once()


def test_upload_file_without_ext():
    sample = mock.Mock(format_name=None)
    api = mock.Mock(**{"upload_samples.return_value": [sample]})
    vxcube_api_cls = mock.Mock(return_value=api)
    runner = CliRunner()
    params = [
        "--base-url", "http://test.url",
        "--version", "42",
        "--api-key", "test-api-key",
        "upload",
        "test_sample_path"
    ]
    with runner.isolated_filesystem():
        with open("test_sample_path", "w") as f:
            f.write("test sample content")
        with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
            result = runner.invoke(cli, params)

    assert normal_execution(result)
    assert "Mock" in result.output
    assert "format not recognized" in result.output
    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.upload_sample.assert_not_called()
    api.upload_samples.assert_called_once()


def test_analyse():
    api = mock.Mock()
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "analyse",
            "23",
            "-p", "winxpx86",
            "--platform", "win7x64",
            "-t", "30",
            "-f", "exe",
            "-c", "CMD_TEST",
            "-g", True,
            "-d", "100",
            "-n", "vpn://",
            "--forwards", "4545",
            "--forwards", "3454:udp",
            "--dump-browsers", False,
            "--dump-mapped", False,
            "--dump-ssdt", False,
            "--dump-processes", False
        ]
        result = runner.invoke(cli, params)
    assert normal_execution(result)
    assert "Mock" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.start_analysis.assert_called_with(
        sample_id=23,
        platforms=("winxpx86", "win7x64"),
        analysis_time=30,
        format_name="exe",
        custom_cmd="CMD_TEST",
        generate_cureit=True,
        drop_size_limit=100,
        net="vpn://",
        copylog=False,
        crypto_api_limit=64,
        dump_size_limit=64,
        flex_time=False,
        forwards=("4545", "3454:udp"),
        get_lib=False,
        injects_limit=100,
        monkey_clicker=False,
        dump_browsers=False,
        dump_mapped=False,
        dump_ssdt=False,
        dump_processes=False,
        no_clean=False,
        optional_count=None,
        proc_lifetime=None,
        set_date=None,
        userbatch=None,
        write_file_limit=512
    )


def test_analyse_all_platforms():
    sample = mock.Mock(platforms=["p1", "p2", "p3"])
    api = mock.Mock(**{"samples.return_value": sample})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "analyse",
            "23",
            "-p", "all",
            "-t", "30",
            "-f", "exe",
            "-c", "CMD_TEST",
            "-g", True,
            "-d", "100",
            "-n", "vpn://",
            "--forwards", "5565"
        ]
        result = runner.invoke(cli, params)
    assert normal_execution(result)
    assert "Mock" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.samples.assert_called_with(sample_id=23)
    api.start_analysis.assert_called_with(
        sample_id=23,
        platforms=["p1", "p2", "p3"],
        analysis_time=30,
        format_name="exe",
        custom_cmd="CMD_TEST",
        generate_cureit=True,
        drop_size_limit=100,
        net="vpn://",
        copylog=False,
        crypto_api_limit=64,
        dump_size_limit=64,
        flex_time=False,
        forwards=("5565",),
        get_lib=False,
        injects_limit=100,
        monkey_clicker=False,
        dump_browsers=True,
        dump_mapped=True,
        dump_ssdt=True,
        dump_processes=True,
        no_clean=False,
        optional_count=None,
        proc_lifetime=None,
        set_date=None,
        userbatch=None,
        write_file_limit=512
    )


def test_delete_analyse():
    analysis = mock.Mock()
    api = mock.Mock(**{"analyses.return_value": analysis})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "delete",
            "some uuid"
        ]
        result = runner.invoke(cli, params)
    assert normal_execution(result)
    assert "Mock" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.analyses.assert_called_with(analysis_id="some uuid")
    analysis.delete.assert_called_once()


def test_subscribe():
    messages = [{
        "task_id": 1,
        "progress": 90,
        "message": u"Legen\u2026"
    }, {
        "task_id": 2,
        "progress": 92,
        "message": u"wait for it\u2026"
    }, {
        "task_id": 1,
        "progress": 100,
        "message": u"dary"
    }, {
        "task_id": 2,
        "progress": 100,
        "message": None
    }]
    analysis = mock.Mock(**{
        "subscribe_progress.return_value": messages,
        "tasks": [mock.Mock(id=1, platform_code="winxpx86"), mock.Mock(id=2, platform_code="win7x64")]
    })
    api = mock.Mock(**{"analyses.return_value": analysis})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "subscribe-analysis",
            "some uuid"
        ]
        result = runner.invoke(cli, params)

    assert normal_execution(result)
    print(result.output)
    assert "Mock" in result.output
    if UTF8_CONSOLE:
        assert "Legen\u2026" in result.output
        assert "wait for it\u2026" in result.output
    else:
        assert "Legen..." in result.output
        assert "wait for it..." in result.output
    assert "dary" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.analyses.assert_called_with(analysis_id="some uuid")


def test_download_sample():
    sample = mock.Mock(spec=Sample, sha1="testsha1")
    api = mock.Mock(**{"samples.return_value": sample})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "sample",
            "--id", "23"
        ]
        result = runner.invoke(cli, params)
        assert normal_execution(result)
        assert "testsha1" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.samples.assert_called_with(sample_id=23, md5=None, sha1=None, sha256=None)


def test_download_samples_by_sha1_with_output():
    sample = mock.Mock(spec=Sample)
    api = mock.Mock(**{"samples.return_value": [sample]})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "sample",
            "--sha1", "23",
            "--output", "test_output"
        ]
        with runner.isolated_filesystem():
            result = runner.invoke(cli, params)

        assert normal_execution(result)
        assert "test_output" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.samples.assert_called_with(sample_id=None, md5=None, sha1="23", sha256=None)


def test_download_sample_multiple_result_with_one_hash():
    sample = mock.Mock(spec=Sample, sha1="testsha1", sha256="testsha256")
    api = mock.Mock(**{"samples.return_value": [sample, sample]})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "sample",
            "--id", "23"
        ]
        result = runner.invoke(cli, params)
        assert normal_execution(result)
        assert "testsha1" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.samples.assert_called_with(sample_id=23, md5=None, sha1=None, sha256=None)


def test_download_sample_multiple_result_with_different_hash():
    sample1 = mock.Mock(spec=Sample, sha1="testsha1", sha256="testsha256")
    sample2 = mock.Mock(spec=Sample, sha1="testsha1-2", sha256="testsha256-2")
    api = mock.Mock(**{"samples.return_value": [sample1, sample2]})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "sample",
            "--id", "23"
        ]
        result = runner.invoke(cli, params)
        assert result.exit_code == 1
        assert "Multiple" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.samples.assert_called_with(sample_id=23, md5=None, sha1=None, sha256=None)


def test_download_sample_by_multiple_parameters():
    sample1 = mock.Mock(spec=Sample, sha1="testsha1", sha256="testsha256")
    sample2 = mock.Mock(spec=Sample, sha1="testsha1-2", sha256="testsha256-2")
    api = mock.Mock(**{"samples.return_value": [sample1, sample2]})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "sample",
            "--id", "23",
            "--md5", "23",
            "--sha1", "23",
            "--sha256", "23"
        ]
        result = runner.invoke(cli, params)
        assert result.exit_code == 2
        assert "Illegal usage" in result.output

    vxcube_api_cls.assert_not_called()
    api.samples.assert_not_called()


def test_download_sample_not_found():
    api = mock.Mock(**{"samples.return_value": ""})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "sample",
            "--id", "23"
        ]
        result = runner.invoke(cli, params)
        assert result.exit_code == 1
        assert "Sample not found" in result.output

    vxcube_api_cls.assert_called_once()
    api.samples.assert_called_once()


def test_download_archive_without_args():
    analysis = mock.Mock()
    api = mock.Mock(**{"analyses.return_value": analysis})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "archive"
        ]
        result = runner.invoke(cli, params)
        assert result.exit_code == 2
        assert "Usage:" in result.output


def test_download_analysis_archive():
    analysis = mock.Mock()
    api = mock.Mock(**{"analyses.return_value": analysis})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "archive",
            "--analysis-id", "some uuid",
            "--output", "test_output"
        ]
        with runner.isolated_filesystem():
            result = runner.invoke(cli, params)

        assert normal_execution(result)
        assert "test_output" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.analyses.assert_called_with(analysis_id="some uuid")
    analysis.download_archive.assert_called_once()


def test_download_task_archive():
    task = mock.Mock()
    api = mock.Mock(**{"task.return_value": task})
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "archive",
            "--task-id", "23",
            "--output", "test_output"
        ]
        with runner.isolated_filesystem():
            result = runner.invoke(cli, params)

        assert normal_execution(result)
        assert "test_output" in result.output

    vxcube_api_cls.assert_called_with(api_key="test-api-key", base_url="http://test.url", version=42)
    api.task.assert_called_with(task_id=23)
    task.download_archive.assert_called_once()


def test_download_archive_multiple_parameters():
    api = mock.Mock()
    vxcube_api_cls = mock.Mock(return_value=api)
    with mock.patch("vxcube_api.cli_helpers.VxCubeApi", new=vxcube_api_cls):
        runner = CliRunner()
        params = [
            "--base-url", "http://test.url",
            "--version", "42",
            "--api-key", "test-api-key",
            "download",
            "archive",
            "--analysis-id", "some uuid",
            "--task-id", "23"
        ]
        result = runner.invoke(cli, params)
        assert result.exit_code == 2
        assert "Illegal usage" in result.output

    vxcube_api_cls.assert_not_called()
    api.samples.assert_not_called()


def test_config_client():
    runner = CliRunner()
    with runner.isolated_filesystem():
        config_path = "test_config.json"
        client_config = ClientConfig(config_path)

        assert client_config.path == config_path
        assert client_config.values == client_config._default_config

        client_config.save(test_param=42)
        assert client_config.test_param == 42
        assert client_config["test_param"] == 42

        with open(config_path) as file:
            data = file.read()
        assert data == "{\"test_param\": 42}"

        client_config2 = ClientConfig(config_path)
        assert client_config2.test_param == 42

        with mock.patch("os.path.exists", return_value=False):
            assert not client_config.delete()
        assert client_config.delete()

        assert client_config.values == client_config._default_config
        assert not os.path.exists(config_path)


def test_save_config():
    client_config = mock.Mock()
    with mock.patch("vxcube_api.__main__.client_config", new=client_config):
        runner = CliRunner()
        params = [
            "config",
            "--api-key", "test-key",
            "--base-url", "http://test.url",
            "--version", "23.42",
        ]
        result = runner.invoke(cli, params)

        assert normal_execution(result)
    client_config.save.assert_called_with(api_key="test-key", base_url="http://test.url", version=23.42)


def test_delete_config():
    client_config = mock.Mock()
    with mock.patch("vxcube_api.__main__.client_config", new=client_config):
        runner = CliRunner()
        params = [
            "config",
            "--delete",
        ]
        result = runner.invoke(cli, params)

        assert normal_execution(result)

    client_config.delete.assert_called_once()


def test_config_bad_parameters():
    runner = CliRunner()
    params = [
        "config",
        "--delete",
        "--api-key", "test-key",
    ]

    result = runner.invoke(cli, params)
    assert result.exit_code == 2
    assert "Illegal usage" in result.output
