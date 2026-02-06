<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\ReportController;

Route::get('/', [ReportController::class, 'index'])->name('report.index');
Route::post('/report/analyze', [ReportController::class, 'analyze'])->name('report.analyze');
Route::post('/report/configure', [ReportController::class, 'configure'])->name('report.configure');
Route::post('/report', [ReportController::class, 'show'])->name('report.show');

