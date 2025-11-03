from ensurepip import bootstrap

from vvecon.zorion import utils

__all__ = ['Files']


class Files(utils.Files):
    common = utils.FileMaker(
    )

    css = utils.FileMaker(
		colors='colors',
		all='all.min',
		animate='animate.min',
		admin='admin',
    )

    js = utils.FileMaker(
		jQuery=('jquery.min', 1, 'util/jquery'),
		slim=('slim', 1, 'util/jquery'),
		popper=('popper', 1, 'util/bootstrap'),
		bootstrap=('bootstrap', 1, 'util/bootstrap'),
		bootstrapBundle=('bootstrap.bundle.min', 1, 'util/bootstrap'),
		main='main',
		style='style',
		loader='Loader',
		models='models',
		api='api',
		util=('util', 1, 'util'),
		moment=('moment.min', 1, 'util/vendor/ui/moment'),
		datePicker=('datepicker.min', 1, 'util/vendor/pickers'),
		dateRangePicker=('daterangepicker', 1, 'util/vendor/pickers'),
		steps=('steps.min', 1, 'util/vendor/forms/wizards'),
		validation=('validate.min', 1, 'util/vendor/forms/validation'),
		autoComplete=('autocomplete.min', 1, 'util/vendor/forms/inputs'),
		select2=('select2.min', 1, 'util/vendor/forms/selects'),
		sweetAlert=('sweet_alert.min', 1, 'util/vendor/notifications'),
		cryptojs=('cryptojs', 1, 'util/vendor/extensions'),
		noUiSlider=('nouislider.min', 1, 'util/vendor/sliders'),
		dataTable=('datatables.min', 1, 'util/vendor/tables/datatables'),
		Model=('Model', 2)
    )

    font = utils.FileMaker(
        poppins='poppins/poppins',
    )

    icon = utils.FileMaker(
        bootstrap='bootstrap/bootstrap-icons.min',
		icomoon='icomoon/styles.min',
		phosphor='phosphor/styles.min',
    )
