import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/bet_parameters.dart';
import '../services/bet_service.dart';

class BetParametersForm extends StatefulWidget {
  final Function(BetParameters) onSubmit;

  const BetParametersForm({
    super.key,
    required this.onSubmit,
  });

  @override
  State<BetParametersForm> createState() => _BetParametersFormState();
}

class _BetParametersFormState extends State<BetParametersForm> {
  final _formKey = GlobalKey<FormState>();
  
  // Form controllers
  final _numBetsController = TextEditingController(text: '3');
  final _minOddsController = TextEditingController(text: '2.0');
  final _maxOddsController = TextEditingController(text: '15.0');
  bool _uniqueMatchOnly = true;
  
  // Track maximum available unique matches
  int _maxAvailableMatches = 10; // Default value
  
  @override
  void initState() {
    super.initState();
    // Get initial value from the bet service if available
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final betService = Provider.of<BetService>(context, listen: false);
      if (betService.maxAvailableMatches > 0) {
        setState(() {
          _maxAvailableMatches = betService.maxAvailableMatches;
        });
      }
    });
  }
  
  @override
  void dispose() {
    _numBetsController.dispose();
    _minOddsController.dispose();
    _maxOddsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final betService = Provider.of<BetService>(context);
    
    // Update max matches if it changes
    if (betService.maxAvailableMatches > 0 && betService.maxAvailableMatches != _maxAvailableMatches) {
      setState(() {
        _maxAvailableMatches = betService.maxAvailableMatches;
      });
    }
    
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _numBetsController,
            decoration: InputDecoration(
              labelText: 'Number of Bets',
              hintText: _uniqueMatchOnly 
                ? 'Enter a number between 1 and $_maxAvailableMatches' 
                : 'Enter a number between 1 and 10',
              helperText: _uniqueMatchOnly 
                ? 'Max available matches: $_maxAvailableMatches' 
                : null,
            ),
            keyboardType: TextInputType.number,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a number';
              }
              final number = int.tryParse(value);
              if (number == null) {
                return 'Please enter a valid number';
              }
              if (number < 1) {
                return 'Number must be at least 1';
              }
              if (_uniqueMatchOnly && number > _maxAvailableMatches) {
                return 'Maximum available matches: $_maxAvailableMatches';
              }
              if (number > 10) {
                return 'Maximum allowed bets: 10';
              }
              return null;
            },
            onChanged: (value) {
              // Force submission when value changes and is valid
              if (_formKey.currentState?.validate() == true) {
                _submitForm();
              }
            },
          ),
          const SizedBox(height: 16),
          
          TextFormField(
            controller: _minOddsController,
            decoration: const InputDecoration(
              labelText: 'Minimum Total Odds',
              hintText: 'Enter a number greater than 1',
            ),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a number';
              }
              final number = double.tryParse(value);
              if (number == null) {
                return 'Please enter a valid number';
              }
              if (number < 1) {
                return 'Number must be at least 1';
              }
              return null;
            },
            onChanged: (value) {
              // Force submission when value changes and is valid
              if (_formKey.currentState?.validate() == true) {
                _submitForm();
              }
            },
          ),
          const SizedBox(height: 16),
          
          TextFormField(
            controller: _maxOddsController,
            decoration: const InputDecoration(
              labelText: 'Maximum Total Odds',
              hintText: 'Enter a number greater than minimum odds',
            ),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a number';
              }
              final number = double.tryParse(value);
              if (number == null) {
                return 'Please enter a valid number';
              }
              final minOdds = double.tryParse(_minOddsController.text) ?? 0;
              if (number <= minOdds) {
                return 'Must be greater than minimum odds';
              }
              return null;
            },
            onChanged: (value) {
              // Force submission when value changes and is valid
              if (_formKey.currentState?.validate() == true) {
                _submitForm();
              }
            },
          ),
          const SizedBox(height: 16),
          
          SwitchListTile(
            title: const Text('Unique Matches Only'),
            subtitle: Text('Limits to $_maxAvailableMatches available matches'),
            value: _uniqueMatchOnly,
            onChanged: (value) {
              setState(() {
                _uniqueMatchOnly = value;
                
                // If switching to unique matches mode and current value exceeds max, adjust it
                if (value) {
                  final currentNum = int.tryParse(_numBetsController.text) ?? 3;
                  if (currentNum > _maxAvailableMatches) {
                    _numBetsController.text = _maxAvailableMatches.toString();
                  }
                }
              });
              // Submit form when switch is toggled
              if (_formKey.currentState?.validate() == true) {
                _submitForm();
              }
            },
          ),
          const SizedBox(height: 16),
          
          ElevatedButton.icon(
            onPressed: betService.isLoading ? null : _submitForm,
            icon: const Icon(Icons.auto_fix_high),
            label: const Text('Generate Bets'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
          const SizedBox(height: 8),
          
          ElevatedButton.icon(
            onPressed: betService.currentBets.isEmpty || betService.isLoading
                ? null
                : () => betService.acceptAllBets(),
            icon: const Icon(Icons.check_circle),
            label: const Text('Accept All'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.secondary,
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
          const SizedBox(height: 8),
          
          ElevatedButton.icon(
            onPressed: !betService.currentBets.any((bet) => bet.isSelected) || betService.isLoading
                ? null
                : () => betService.rejectSelectedBets(),
            icon: const Icon(Icons.cancel),
            label: const Text('Reject Selected'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ],
      ),
    );
  }
  
  void _submitForm() {
    if (_formKey.currentState!.validate()) {
      final params = BetParameters(
        numBets: int.parse(_numBetsController.text),
        minOdds: double.parse(_minOddsController.text),
        maxOdds: double.parse(_maxOddsController.text),
        uniqueMatchOnly: _uniqueMatchOnly,
      );
      
      widget.onSubmit(params);
    }
  }
}
