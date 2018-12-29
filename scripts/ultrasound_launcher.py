# tf_unet is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# tf_unet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with tf_unet.  If not, see <http://www.gnu.org/licenses/>.


'''
Created on Jul 28, 2016

author: jakeret

Trains a tf_unet network to segment nerves in the Ultrasound Kaggle Dataset.
Requires the Kaggle dataset.
'''

from __future__ import print_function, division, absolute_import, unicode_literals
import os
import click
import numpy as np

from tf_unet import unet
from tf_unet import util
from tf_unet.image_util import ImageDataProvider


@click.command()
@click.option('--data_root', default="../../ultrasound/train")
@click.option('--output_path', default="./unet_trained_ultrasound")
@click.option('--training_iters', default=32)
@click.option('--epochs', default=100)
@click.option('--restore', default=False)
@click.option('--layers', default=5)
@click.option('--features_root', default=64)
def launch(data_root, output_path, training_iters, epochs, restore, layers, features_root):
    print("Using data from: %s"%data_root)

    if not os.path.exists(data_root):
        raise IOError("Kaggle Ultrasound Dataset not found")

    data_provider = DataProvider(data_root + "/*.tif",
                                 a_min=0,
                                 a_max=210)
    net = unet.Unet(channels=data_provider.channels, 
                    n_class=data_provider.n_class, 
                    layers=layers, 
                    features_root=features_root,
                    cost="dice_coefficient",
                    )
    
    path = output_path if restore else util.create_training_path(output_path)

    trainer = unet.Trainer(net, norm_grads=True, optimizer="adam")
    path = trainer.train(data_provider, path, 
                         training_iters=training_iters, 
                         epochs=epochs, 
                         dropout=0.5, 
                         display_step=2, 
                         restore=restore)
     
    x_test, y_test = data_provider(1)
    prediction = net.predict(path, x_test)
     
    print("Testing error rate: {:.2f}%".format(unet.error_rate(prediction, util.crop_to_shape(y_test, prediction.shape))))
    

if __name__ == '__main__':
    launch()


class DataProvider(ImageDataProvider):
    """
    Extends the default ImageDataProvider to randomly select the next
    image and ensures that only data sets are used where the mask is not empty
    """

    def _next_data(self):
        data, mask = super(DataProvider, self)._next_data()
        while mask.sum() == 0:
            self._cylce_file()
            data, mask = super(DataProvider, self)._next_data()

        return data, mask


    def _cylce_file(self):
        self.file_idx = np.random.choice(len(self.data_files))