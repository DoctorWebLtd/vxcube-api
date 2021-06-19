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

import logging
import os
import sys

import click

from vxcube_api.api import VxCubeApi
from vxcube_api.cli_helpers import client_config, Mutex, ApiInfo, pass_api_info, pass_api
from vxcube_api.errors import VxCubeApiException
from vxcube_api.objects import Sample
from vxcube_api.utils import message_compat, root_logger_setup


logger = logging.getLogger(__name__)


@click.group()
@click.option("--api-key", default=client_config.api_key, show_default=True, cls=Mutex, not_required_if=["config",
                                                                                                         "login"])
@click.option("--base-url", default=client_config.base_url, show_default=True, cls=Mutex, not_required_if=["config"])
@click.option("--version", default=client_config.version, show_default=True, cls=Mutex, not_required_if=["config"])
@click.option("--verbose", "-v", default=False, is_flag=True, help="Enable verbose mode")
@click.pass_context
def cli(ctx, api_key, base_url, version, verbose):
    root_logger_setup(level=logging.DEBUG if verbose else logging.INFO)
    ctx.obj = ApiInfo(api_key, base_url, version)


@cli.group("download")
def download():
    """Download files."""
    pass


@cli.command("config")
@click.option("--delete", is_flag=True, cls=Mutex, not_required_if=["api_key", "base_url", "version"])
@click.option("--api-key", default=client_config.api_key, cls=Mutex, not_required_if=["delete"])
@click.option("--base-url", default=client_config.base_url, show_default=True, cls=Mutex, not_required_if=["delete"])
@click.option("--version", default=client_config.version, show_default=True, cls=Mutex, not_required_if=["delete"])
def save_config(delete, api_key, base_url, version):
    """Use config file for saving default values (api-key, base-url, and version)."""
    if delete:
        logger.info("Trying to delete config...")
        if client_config.delete():
            logger.info("Config deleted successfully")
        else:
            logger.warning("Config unable deleted")
    else:
        client_config.save(api_key=api_key, base_url=base_url, version=version)


@cli.command("login")
@click.option("--login", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--new-key", default=False, is_flag=True)
@pass_api_info
def get_token(api_info, login, password, new_key):
    """Get API key by login and password."""
    api = VxCubeApi(base_url=api_info.base_url, version=api_info.version)
    api.login(login=login, password=password, new_key=new_key)
    logger.info("Session started with API key {}".format(api._raw_api.api_key))


@cli.command("upload")
@click.argument("sample-path", type=click.File("rb"))
@pass_api
def upload_sample(api, sample_path):
    """Upload sample to Dr.Web vxCube server."""
    sample = api.upload_sample(file=sample_path)
    logger.info("Sample uploaded successfully:")
    logger.info("\t{sample.name} [id: {sample.id}]".format(sample=sample))
    if sample.format_name:
        logger.info("\t - format: {sample.format_name}\n"
                    "\t - platforms: {sample.platforms}"
                    "".format(sample=sample))
    else:
        logger.warning("File format not recognized: specify format when starting analysis")


@cli.command("analyse")
@click.argument("sample-id", type=int)
@click.option("-p", "--platform", multiple=True, required=True,
              help="Use 'all' to analyse on all available platforms")
@click.option("-t", "--time", default=60, help="Sample analysis time in seconds")
@click.option("-f", "--format", default=None, help="Sample format name")
@click.option("-c", "--cmd", default=None, help="Specific sample analysis command")
@click.option("-g", "--generate-cureit", default=False, help="Generate CureIt!")
@click.option("-d", "--drop-size-limit", default=64, help="Total size limit for drops, MB")
@click.option("-n", "--net", default="vpn://", help="Proxy parameters")
@pass_api
def analyse(api, sample_id, platform, time, format, cmd, generate_cureit, drop_size_limit, net):
    """Start analysis by sample ID."""
    if "all" in platform:
        sample = api.samples(sample_id=sample_id)
        platform = sample.platforms

    analysis = api.start_analysis(
        sample_id=sample_id,
        platforms=platform,
        analysis_time=time,
        format_name=format,
        custom_cmd=cmd,
        generate_cureit=generate_cureit,
        drop_size_limit=drop_size_limit,
        net=net
    )
    logger.info("Analysis {analysis.id} started".format(analysis=analysis))


@cli.command("subscribe-analysis")
@click.argument("analysis-id", type=int)
@pass_api
def subscribe(api, analysis_id):
    """Get real-time data about analysis progress."""
    analysis = api.analyses(analysis_id=analysis_id)
    tasks_msg = {}
    for i, task in enumerate(analysis.tasks):
        tasks_msg[task.id] = "[{task.platform_code:<8}] [{{progress}}%] {{message}}".format(task=task)

    if analysis.is_processing:
        for progress_args in analysis.subscribe_progress():
            if "message" in progress_args:
                progress_args["message"] = message_compat(progress_args["message"])
            logging.info(tasks_msg[progress_args["task_id"]].format(**progress_args))

    msg = "Task[{task.id}]-{task.platform_code} [{task.status}] maliciousness: {task.maliciousness}"
    logging.info("All tasks finished:")
    for task in analysis.tasks:
        logging.info(msg.format(task=task))


@cli.command("delete")
@click.argument("analysis-id", type=int)
@pass_api
def delete_analysis(api, analysis_id):
    """Delete analysis by ID."""
    analysis = api.analyses(analysis_id=analysis_id)
    analysis.delete()
    logging.info("Analysis {analysis.id} successfully deleted".format(analysis=analysis))


@download.command("sample")
@click.option("--id", type=int, cls=Mutex, not_required_if=["md5", "sha1", "sha256"])
@click.option("--md5", type=str, cls=Mutex, not_required_if=["id", "sha1", "sha256"])
@click.option("--sha1", type=str, cls=Mutex, not_required_if=["id", "md5", "sha256"])
@click.option("--sha256", type=str, cls=Mutex, not_required_if=["id", "md5", "sha1"])
@click.option("-o", "--output", type=click.File("wb"))
@pass_api
def download_sample(api, id, md5, sha1, sha256, output):
    """Download sample by ID, MD5, SHA1, or SHA256."""
    samples = api.samples(sample_id=id, md5=md5, sha1=sha1, sha256=sha256)
    if isinstance(samples, Sample):
        sample = samples
    elif isinstance(samples, list) and len(samples) == 1:
        sample = samples[0]
    elif len(samples) > 1:
        sha256 = samples[0].sha256
        if all(sample.sha256 == sha256 for sample in samples):
            sample = samples[0]
        else:
            logging.info("Multiple samples found:")
            sha256 = set()
            for sample in samples:
                if sample.sha256 not in sha256:
                    sha256.add(sample.sha256)
                    logging.info(
                        "\t {sample.name} [id: {sample.id}]"
                        "\n\t - md5: {sample.md5}"
                        "\n\t - sha1: {sample.sha1}"
                        "\n\t - sha256: {sample.sha256}"
                        "\n".format(sample=sample))
            return exit(1)
    else:
        logging.error("Sample not found")
        return exit(1)

    output = output or sample.sha1
    sample.download(output)

    if hasattr(output, "name"):
        output = output.name
    logging.info("Sample downloaded to {}.".format(
        os.path.join(os.getcwd(), output) if not os.path.isabs(output) else output
    ))


@download.command("archive")
@click.option("--analysis-id", cls=Mutex, not_required_if=["task_id"], type=int)
@click.option("--task-id", cls=Mutex, not_required_if=["analyse_id"], type=int)
@click.option("-o", "--output", type=click.File("wb"))
@pass_api
def download_analyse_archive(api, analysis_id, task_id, output):
    """Download analysis archive or task archive."""
    if analysis_id:
        analysis = api.analyses(analysis_id=analysis_id)
        output = output or "{sha1}_archive.zip".format(sha1=analysis.sha1)
        analysis.download_archive(output)
    elif task_id:
        task = api.task(task_id=task_id)
        output = output or "{pl}_archive.zip".format(pl=task.platform_code)
        task.download_archive(output)
    else:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(2)

    if hasattr(output, "name"):
        output = output.name

    logging.info("Archive downloaded to {}.".format(
        os.path.join(os.getcwd(), output) if not os.path.isabs(output) else output
    ))


def main():
    try:
        cli()
        sys.exit(0)
    except VxCubeApiException as e:
        logging.error("API error: {}".format(str(e)))
        sys.exit(-1)
    except KeyboardInterrupt:
        logging.warning("Interrupted by user")
        sys.exit(-2)
    except Exception as e:
        logging.exception("Unknown error: {}".format(str(e)))
        sys.exit(-3)


if __name__ == "__main__":
    main()
