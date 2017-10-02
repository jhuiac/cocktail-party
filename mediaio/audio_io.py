from scipy.io import wavfile
import numpy as np


class AudioSignal:

	def __init__(self, data, sample_rate):
		self._data = np.copy(data)
		self._sample_rate = sample_rate

	@staticmethod
	def from_wav_file(wave_file_path):
		sample_rate, data = wavfile.read(wave_file_path)
		return AudioSignal(data, sample_rate)

	def save_to_wav_file(self, wave_file_path):
		wavfile.write(wave_file_path, self._sample_rate, self._data)

	def get_data(self, channel_index=None):
		# data shape: (n_samples) or (n_samples, n_channels)

		if channel_index is None:
			return self._data

		if channel_index not in range(self.get_number_of_channels()):
			raise IndexError("invalid channel index")

		if channel_index == 0 and self.get_number_of_channels() == 1:
			return self._data

		return self._data[:, channel_index]

	def get_number_of_samples(self):
		return self._data.shape[0]

	def get_number_of_channels(self):
		# data shape: (n_samples) or (n_samples, n_channels)

		if len(self._data.shape) == 1:
			return 1

		return self._data.shape[1]

	def get_sample_rate(self):
		return self._sample_rate

	def get_sample_type(self):
		return self._data.dtype

	def get_format(self):
		return dict(
			n_channels=self.get_number_of_channels(),
			sample_rate=self.get_sample_rate(),
			sample_type=self.get_sample_type()
		)

	def get_length_in_seconds(self):
		return float(self.get_number_of_samples()) / self.get_sample_rate()

	def set_sample_type(self, sample_type, equalize):
		sample_type_info = np.iinfo(sample_type)

		if equalize:
			equalization_factor = float(sample_type_info.max) / np.abs(self._data).max()
			self._data *= equalization_factor

		self._data = self._data.clip(sample_type_info.min, sample_type_info.max).astype(sample_type)

	def split(self, n_slices):
		return [AudioSignal(s, self._sample_rate) for s in np.split(self._data, n_slices)]

	def slice(self, start_sample_index, end_sample_index):
		return AudioSignal(self._data[start_sample_index:end_sample_index], self._sample_rate)

	def pad_with_zeros(self, new_length):
		if self.get_number_of_samples() > new_length:
			raise Exception("cannot zero-pad for shorter signal length")

		new_shape = list(self._data.shape)
		new_shape[0] = new_length

		self._data = np.copy(self._data)
		self._data.resize(new_shape)

	def truncate(self, new_length):
		if self.get_number_of_samples() < new_length:
			raise Exception("cannot truncate for longer signal length")

		self._data = self._data[:new_length]

	@staticmethod
	def concat(signals):
		for signal in signals:
			if signal.get_format() != signals[0].get_format():
				raise Exception("concating audio signals with different formats is not supported")

		data = [signal.get_data() for signal in signals]
		return AudioSignal(np.concatenate(data), signals[0].get_sample_rate())


class AudioMixer:

	@staticmethod
	def mix(audio_signals, mixing_weights=None):
		if mixing_weights is None:
			mixing_weights = [1] * len(audio_signals)

		reference_signal = audio_signals[0]

		mixed_data = np.zeros(shape=reference_signal.get_data().shape, dtype=float)
		for i, signal in enumerate(audio_signals):
			if signal.get_format() != reference_signal.get_format():
				raise Exception("mixing audio signals with different format is not supported")

			mixed_data += (float(mixing_weights[i])) * signal.get_data()

		mixed_audio_signal = AudioSignal(mixed_data, reference_signal.get_sample_rate())
		mixed_audio_signal.set_sample_type(reference_signal.get_sample_type(), equalize=False)

		return mixed_audio_signal
