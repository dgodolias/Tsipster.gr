import 'package:flutter/material.dart';

class ImageHelper {
  /// Loads an asset image with error handling
  static Widget loadAsset(String path, {double? height, double? width, Color? color, BoxFit fit = BoxFit.contain}) {
    return Image.asset(
      path,
      height: height,
      width: width,
      color: color,
      fit: fit,
      errorBuilder: (context, error, stackTrace) {
        debugPrint('Error loading image $path: $error');
        // Return a placeholder or fallback image
        return Container(
          height: height,
          width: width,
          color: Colors.grey.shade200,
          child: Icon(
            Icons.image_not_supported,
            color: Colors.grey.shade600,
            size: height != null ? height * 0.6 : 24,
          ),
        );
      },
    );
  }
}
