#emacs: -*- mode: python-mode; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the PyMVPA package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Common to all SVM implementations functionality. For internal use only"""

__docformat__ = 'restructuredtext'

import numpy as N

from copy import deepcopy

from mvpa.misc import warning
from mvpa.clfs.classifier import Classifier
from mvpa.misc.param import Parameter

if __debug__:
    from mvpa.misc import debug

class _SVM(Classifier):
    """Support Vector Machine Classifier.

    Base class for all external SVM implementations.

    Derived classes should define:

    * _KERNELS: map(dict) should define assignment to internal kernel type
      e.g. _KERNELS = { 'linear': shogun.Kernel.LinearKernel, ... }

    """

    _ATTRIBUTE_COLLECTIONS = ['params', 'kernel_params'] # enforce presence of params collections

    _SVM_PARAMS = {
        'C' : Parameter(-1.0, min=1e-10, descr='Trade-off parameter. High C -- rigid margin SVM'),
        'nu' : Parameter(0.5, min=0.0, max=1.0, descr='Fraction of datapoints within the margin'),
        'cache_size': Parameter(100, descr='Size of the kernel cache, specified in megabytes'),
        'coef0': Parameter(0.0, descr='Offset coefficient in polynomial and sigmoid kernels'),
        'degree': Parameter(3, descr='Degree of polynomial kernel'),
        'p': Parameter(0.1, descr='Epsilon in epsilon-insensitive loss function of epsilon-SVM regression'),
        'gamma': Parameter(0, descr='Scaling (width in RBF) within non-linear kernels'),
        'max_shift': Parameter(10.0, min=0.0, descr='Maximal shift for SGs GaussianShiftKernel'),
        'shift_step': Parameter(1.0, min=0.0, descr='Shift step for SGs GaussianShiftKernel'),
        'probability': Parameter(0, descr='Flag to signal either probability estimate is obtained within LibSVM'),
        'shrinking': Parameter(1, descr='Either shrinking is to be conducted'),
        'weight_label': Parameter([], descr='???'),
        'weight': Parameter([], descr='???'),
        'epsilon': Parameter(5e-5,  # XXX it used to work fine with 1e-5 but after Yariks
                                    # evil RF it got slowed down too much. 
                        min=1e-10,
                        descr='Tolerance of termination criterium')
        }


    def __init__(self, kernel_type='linear', **kwargs):
        """Init base class of SVMs. *Not to be publicly used*

        :Parameters:
          kernel_type : basestr
            String must be a valid key for cls._KERNELS
        """

        kernel_type = kernel_type.lower()
        if not kernel_type in self._KERNELS:
            raise ValueError, "Unknown kernel " + kernel_type

        # Add corresponding kernel parameters to 'known' depending on what
        # kernel was chosen
        if self._KERNELS[kernel_type][1] is not None:
            # XXX need to do only if it is a class variable
            self._KNOWN_KERNEL_PARAMS = \
                 self._KNOWN_KERNEL_PARAMS[:] + list(self._KERNELS[kernel_type][1])

        # pop out all args from **kwargs which are known to be SVM parameters
        _args = {}
        for param in self._KNOWN_KERNEL_PARAMS + self._KNOWN_PARAMS:
            if param in kwargs:
                _args[param] = kwargs.pop(param)

        Classifier.__init__(self, **kwargs)

        for paramfamily, paramset in ( (self._KNOWN_PARAMS, self.params),
                                       (self._KNOWN_KERNEL_PARAMS, self.kernel_params)):
            for paramname in paramfamily:
                if not (paramname in self._SVM_PARAMS):
                    raise ValueError, "Unknown parameter %s" % paramname
                param = deepcopy(self._SVM_PARAMS[paramname])
                param.name = paramname
                if paramname in _args:
                    param.value = _args[paramname]
                    # XXX UGLY!
                    #param._default = _args[paramname]
                    #param._isset = False

                paramset.add(param)

        self._kernel_type = self._KERNELS[kernel_type][0]
        if __debug__:
            debug("SVM", "Initialized %s with kernel %s:%s" % 
                  (id(self), kernel_type, self._kernel_type))

        # XXX might want to create a Parameter with a list of
        # available kernels?
        self._kernel_type_literal = kernel_type


    def _getDefaultC(self, data):
        """Compute default C

        TODO: for non-linear SVMs
        """

        if self._kernel_type_literal == 'linear':
            datasetnorm = N.mean(N.sqrt(N.sum(data*data, axis=1)))
            value = 1.0/(datasetnorm*datasetnorm)
            if __debug__:
                debug("SVM", "Default C computed to be %f" % value)
        else:
            warning("TODO: Computation of default C is not yet implemented" +
                    " for non-linear SVMs. Assigning 1.0")
            value = 1.0

        return value


