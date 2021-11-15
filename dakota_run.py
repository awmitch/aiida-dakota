from aiida import orm, engine
from aiida.common.exceptions import NotExistent
from aiida.plugins import DataFactory, CalculationFactory

parameters = {
	'Sim Params':{
		'profileType': "CC",
		'Crate': 1,
		'Vmax': 3.6,
		'Vmin': 2.0,
		'Vset': 0.12,
		'power': 1,
		'segments': "[(0.3,0.4),(-0.5,0.1)]",
		'prevDir': "false",
		'tend': 1.2e3,
		'tsteps': 200,
		'relTol': 1e-6,
		'absTol': 1e-6,
		'T': 298,
		'randomSeed': "false",
		'seed': 0,
		'dataReporter': "hdf5",
		'Rser': 0.,
		'Nvol_c': 10,
		'Nvol_s': 5,
		'Nvol_a': 10,
		'Npart_c': 2,
		'Npart_a': 2,
	},
	'Electrodes':{
		'cathode': "template_c.in",
		'anode': "template_a.in",
		'k0_foil': 1e0,
		'Rfilm_foil': 0e-0,

	},
	'Particles':{
		'mean_c': 100e-9,
		'stddev_c': 1e-9,
		'mean_a': 100e-9,
		'stddev_a': 1e-9,
		'specified_psd_c': "false",
		'specified_psd_a': "false",
		'cs0_c': 0.01,
		'cs0_a': 0.99,
	},
	'Conductivity':{
		'simBulkCond_c': "false",
		'simBulkCond_a': "false",
		'sigma_s_c': 1e-1,
		'sigma_s_a': 1e-1,
		'simPartCond_c': "false",
		'simPartCond_a': "false",
		'G_mean_c': 1e-14,
		'G_stddev_c': 0,
		'G_mean_a': 1e-14,
		'G_stddev_a': 0,
	},
	'Geometry':{
		'L_c': 50e-6,
		'L_a': 50e-6,
		'L_s': 25e-6,
		'P_L_c': 0.69,
		'P_L_a': 0.69,
		'poros_c': 0.4,
		'poros_a': 0.4,
		'poros_s': 1.0,
		'BruggExp_c': -0.5,
		'BruggExp_a': -0.5,
		'BruggExp_s': -0.5,
	},
	'Electrolyte':{
		'c0': 1000,
		'zp': 1,
		'zm': -1,
		'nup': 1,
		'num': 1,
		'elyteModelType': "SM",
		'SMset': "valoen_bernardi",
		'n': 1,
		'sp': -1,
		'Dp': 2.2e-10,
		'Dm': 2.94e-10,
	},
}

cathode_parameters = {
	'Particles': {
		'type': "ACR",
		'discretization': 1e-9,
		'shape': "C3",
		'thickness': 20e-9,
	},
	'Material': {
		'muRfunc': "LiFePO4",
		'logPad': "false",
		'noise': "false",
		'noise_prefac': 1e-6,
		'numnoise': 200,
		'Omega_a': 1.8560e-20,
		'kappa': 5.0148e-10,
		'B': 0.1916e9,
		'rho_s': 1.3793e28,
		'D': 5.3e-19,
		'Dfunc': "lattice",
		'dgammadc': 0e-30,
		'cwet': 0.98,
	},
	'Reactions': {
		'rxnType': "BV",
		'k0': 1.6e-1,
		'E_A': 13000,
		'alpha': 0.5,
		# Fraggedakis et al. 2020, lambda: 8.3kBT
		'lambda': 3.4113e-20,
		'Rfilm': 0e-0,
	},
}
anode_parameters = {
	'Particles': {
		'type': "CHR",
		'discretization': 2.5e-8,
		'shape': "cylinder",
		'thickness': 20e-9,
	},
	'Material': {
		'muRfunc': "LiC6_1param",
		'logPad': "false",
		'noise': "false",
		'noise_prefac': 1e-6,
		'numnoise': 200,
		'Omega_a': 1.3992e-20,
		'Omega_b': 5.761532e-21,
		'kappa': 4.0e-7,
		'B': 0.0,
		'rho_s': 1.7e28,
		'D': 1.25e-12,
		'Dfunc': "lattice",
		'dgammadc': 0e-30,
		'cwet': 0.98,
	},
	'Reactions': {
		'rxnType': "BV",
		'k0': "{k0}",
		# 'k0': 3.0e+1,
		'E_A': 50000,
		'alpha': 0.5,
		# Fraggedakis et al. 2020, lambda: 8.3kBT
		'lambda': 2.055e-20,
		'Rfilm': 0e-0,
	},
}

# Setting up inputs
computer = orm.load_computer('workstation')
try:
    code = load_code('mpet@workstation')
except NotExistent:
    # Setting up code via python API (or use "verdi code setup")
    code = orm.Code(label='workstation', remote_computer_exec=[computer, '/bin/bash'], input_plugin_name='mpet.mpetrun')
builder = code.get_builder()
builder.parameters = Dict(dict=parameters)
builder.cathode_parameters = Dict(dict=cathode_parameters)
builder.anode_parameters = Dict(dict=anode_parameters)
builder.metadata.options.withmpi = True
builder.metadata.options.resources = {
    'num_machines': 1,
    'num_mpiprocs_per_machine': 1,
}

builder.metadata.dry_run = True
builder.metadata.store_provenance = True
builder.metadata.options.input_filename = 'template.in'
builder.metadata.options.cathode_input_filename = 'template_c.in'
builder.metadata.options.anode_input_filename = 'template_a.in'
builder.metadata.options.submit_script_filename = 'driver.sh'
builder.metadata.options.prepend_text = 'mv template_a.in template_a_old.in; dprepro3 --left-delimiter="{" --right-delimiter="}" $1 template_a_old.in template_a.in'
result, calc = engine.run_get_node(builder)
abspath = calc._raw_input_folder.abspath 

SingleFileData = DataFactory('singlefile')
driver = SingleFileData(abspath + '/driver.sh')
print(abspath)
parameters = {
	'environment':{
		'keywords':["tabular_data"],
		'tabular_data_file':"List_param_study.dat",
	},
	'method':{
		'id_method': "method1",
		'keywords':["list_parameter_study"],
		'list_of_points':[30, 50],

	},
	'model':{
		'keywords':["single"],
		'id_model': "model1",
		'interface_pointer': "interface1",
		'variables_pointer': "variables1",
		'responses_pointer': "responses1",
	},
	'variables':{
		'keywords':[],
		'id_variables': "variables1",
		'continuous_design':1,
		'descriptors': "k0",
	},
	'interface':{
		'keywords':["fork", "file_tag", "file_save", "directory_save", "dprepro", "work_directory", "directory_tag", "deactivate", "active_set_vector"],
		'id_interface': "interface1",
		'analysis_driver': "/bin/bash driver.sh",
		'parameters_file': "params.out",
		'results_file': "results.out",
		'copy_files': [f"{abspath + '/driver.sh'}",f"{abspath + '/template.in'}",f"{abspath + '/template_c.in'}",f"{abspath + '/template_a.in'}"],
		'named': "workdir"
	},
	'responses':{
		'keywords':["no_gradients", "no_hessians"],
		'id_responses': "responses1",
		'response_functions':1,
	},
}

# Setting up inputs
computer = orm.load_computer('workstation')

code = load_code('dakota@workstation')

builder = code.get_builder()
builder.parameters = Dict(dict=parameters)
builder.driver = driver
builder.metadata.options.driver_filename = 'driver.sh'
builder.metadata.options.withmpi = False
builder.metadata.options.resources = {
    'num_machines': 1,
    'num_mpiprocs_per_machine': 1,
}

# Running the calculation & parsing results
#output_dict, node = engine.run_get_node(builder)
result, calc = engine.run_get_node(builder)
abspath = calc._raw_input_folder.abspath 
print(abspath)
print("Completed.")