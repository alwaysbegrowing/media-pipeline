

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
        self.outputs = 0

    # add input to the job
    def add_input(self, bucket, input_name):
        self.inputs.append({"bucket": bucket, "name": input_name})

    # add output to the job
    def add_output(self, bucket, output_name, bitrate=12000000, crop=None):
        self.outputs.append(
            {"bucket": bucket, "modifier": output_name, "bitrate": bitrate, "crop": crop})

    # construct output group
    def _construct_output_group(self, output):
        self.outputs += 1
        return {
            "Name": f"File Group {self.outputs}",
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
                    "Crop": output["crop"]
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
        job = {
            "Queue": self.queue_arn,
            "UserMetadata": {},
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
