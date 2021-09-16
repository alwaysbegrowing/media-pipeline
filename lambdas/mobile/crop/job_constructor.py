

class MCJob:

    # create crop static method
    @staticmethod
    def create_crop(x, y, width, height):
        return {"X": x, "Y": y, "Width": width, "Height": height}

    # initialize the job
    def __init__(self, queue_arn, role_arn):
        self.inputs = []
        self.outputs = []
        self.queue_arn = queue_arn
        self.role_arn = role_arn
        self.n = 0

    def add_task_token(self, task_token):
        self.task_token = task_token

    # add input to the job
    def add_input(self, bucket, input_name):
        self.inputs.append({"bucket": bucket, "name": input_name})

    # add output to the job
    def add_output(self, bucket, output_name, width, height, bitrate=12_000_000, crop=None):
        self.outputs.append(
            {"bucket": bucket, "modifier": output_name, "width": width, "height": height, "bitrate": bitrate, "crop": crop})

    # construct output group
    def _construct_output_group(self, output):
        self.n += 1
        return {
            "Name": f"File Group {self.n}",
            "Outputs": [{
                "ContainerSettings": {
                    "Container": "MP4",
                    "Mp4Settings": {}
                },
                "VideoDescription": {
                    "CodecSettings": {
                        "Codec": "H_264",
                        "H264Settings": {
                            "MaxBitrate": output["bitrate"],
                            "RateControlMode": "QVBR",
                            "SceneChangeDetect": "TRANSITION_DETECTION"
                        }
                    },
                    "Crop": output["crop"],
                    "Width": output["width"],
                    "Height": output["height"],
                },
                "AudioDescriptions": [{
                    "CodecSettings": {
                        "Codec": "AAC",
                        "AacSettings": {
                            "Bitrate": 96000,
                            "CodingMode": "CODING_MODE_2_0",
                            "SampleRate": 48000
                        }
                    }
                }],
                "NameModifier": output["modifier"],
            }],
            "OutputGroupSettings": {
                "Type": "FILE_GROUP_SETTINGS",
                "FileGroupSettings": {
                    "Destination": f"s3://{output['bucket']}"
                }
            }
        }

    # construct input groups
    def _construct_input_group(self, input_video):
        return {
            "AudioSelectors": {
                "Audio Selector 1": {
                    "DefaultSelection": "DEFAULT"
                }
            },
            "VideoSelector": {},
            "TimecodeSource": "ZEROBASED",
            "FileInput": f"s3://{input_video['bucket']}/{input_video['name']}"
        }

    # create job
    def create(self):
        task_token1 = self.task_token[0:256]
        task_token2 = self.task_token[256:512]
        task_token3 = self.task_token[512:768]
        job = {
            "UserMetadata": {
                "TaskToken1": task_token1,
                "TaskToken2": task_token2,
                "TaskToken3": task_token3
            },
            "Queue": self.queue_arn,
            "Role": self.role_arn,
            "Settings": {
                "TimecodeConfig": {
                    "Source": "ZEROBASED"
                },
                "OutputGroups": [],
                "Inputs": []
            },
            "AccelerationSettings": {
                "Mode": "DISABLED"
            },
            "StatusUpdateInterval": "SECONDS_60",
            "Priority": 0
        }

        # add inputs
        for input in self.inputs:
            job["Settings"]["Inputs"].append(
                self._construct_input_group(input))

        # add outputs
        for output in self.outputs:
            job["Settings"]["OutputGroups"].append(
                self._construct_output_group(output))

        return job


if __name__ == "__main__":
    import json
    job = MCJob(
        "arn:aws:sqs:us-east-1:123456789012:MyQueue",  # queue arn
        "arn:aws:iam::123456789012:role/MyRole"  # role arn
    )

    # add inputs
    job.add_input(
        "chandlerstestbucket",  # bucket name
        "Input.mp4"  # input name
    )

    # add outputs
    job.add_output(
        "chandlerstestbucket",  # bucket name
        "Background",  # output name
        1080,  # width
        1920,  # height
        bitrate=4_000_000,  # bitrate
        crop=MCJob.create_crop(656, 0, 608, 1080)  # crop
    )

    job.add_output(
        "chandlerstestbucket",  # bucket name
        "Content",  # output name
        1080,  # width
        1080,  # height
        bitrate=5_000_000,  # bitrate
        crop=MCJob.create_crop(456, 18, 1000, 1000)  # crop
    )

    job.add_output(
        "chandlerstestbucket",  # bucket name
        "Facecam",  # output name
        560,
        420,
        bitrate=2_000_000,
        crop=MCJob.create_crop(1420, 778, 400, 300)
    )

    with open('test.json', 'w') as f:
        json.dump(job.create(), f, indent=4)
